# services/saga_coordinator/app/services/saga_service.py

from uuid import UUID
from typing import List, Optional

from src.domain.entities.saga_instance import SagaInstance, SagaStatus
from src.domain.ports.saga_instance_repository import SagaRepositoryPort


class SagaService:
    """Сервис для управления жизненным циклом SagaInstance"""

    def __init__(
            self,
            repository: SagaRepositoryPort,
    ):
        self._repository = repository

    # ---- CRUD / Basic Operations ----

    async def create(self, saga: SagaInstance) -> SagaInstance:
        """
        Создать новый инстанс саги.
        Используется при получении стартового события (например, ShipmentCreated).
        """
        # Можно добавить проверку на существование дубликата, если бизнес-логика требует
        # unique constraint на shipment_id
        return await self._repository.save(saga)

    async def get(self, saga_id: UUID) -> Optional[SagaInstance]:
        """Получить сагу по ID."""
        return await self._repository.get(saga_id)

    async def get_by_shipment(self, shipment_id: UUID) -> Optional[SagaInstance]:
        """Получить активную сагу для конкретного отправления."""
        return await self._repository.get_by_shipment(shipment_id)

    async def list_active_sagas(self) -> List[SagaInstance]:
        """
        Получить все незавершенные саги.
        Полезно для воркеров восстановления после сбоев.
        """
        return await self._repository.list_active()

    # ---- State Transitions (Business Logic) ----

    async def update_context(self, saga_id: UUID, **kwargs) -> SagaInstance:
        """
        Обновить контекст саги (привязать warehouse_id, delivery_id и т.д.).

        Args:
            saga_id: ID саги
            **kwargs: Поля для обновления (warehouse_id, delivery_id)
        """
        saga = await self._repository.get(saga_id)
        if not saga:
            raise ValueError(f"Saga {saga_id} not found")

        # Динамическое обновление полей, если они есть в сущности
        updated = False
        if 'warehouse_id' in kwargs and kwargs['warehouse_id']:
            saga.warehouse_id = kwargs['warehouse_id']
            updated = True

        if 'delivery_id' in kwargs and kwargs['delivery_id']:
            saga.delivery_id = kwargs['delivery_id']
            updated = True

        if updated:
            return await self._repository.save(saga)
        return saga

    async def complete_saga(self, saga_id: UUID) -> SagaInstance:
        """
        Завершить сагу успешно.
        """
        saga = await self._repository.get(saga_id)
        if not saga:
            raise ValueError(f"Saga {saga_id} not found")

        if saga.status != SagaStatus.STARTED:
            # Логируем или игнорируем, если уже завершена
            return saga

        saga.mark_completed()
        return await self._repository.save(saga)

    async def fail_saga(self, saga_id: UUID, step: str, error_message: str) -> SagaInstance:
        """
        Перевести сагу в статус FAILED (без компенсации или после неё).
        """
        saga = await self._repository.get(saga_id)
        if not saga:
            raise ValueError(f"Saga {saga_id} not found")

        saga.mark_failed(step=step, error=error_message)
        return await self._repository.save(saga)

    async def trigger_compensation(self, saga_id: UUID, failed_step: str) -> SagaInstance:
        """
        Перевести сагу в режим компенсации (COMPENSATING).
        Вызывается воркером при обнаружении ошибки, требующей отката.
        """
        saga = await self._repository.get(saga_id)
        if not saga:
            raise ValueError(f"Saga {saga_id} not found")

        # Нельзя начать компенсацию, если она уже завершена
        if saga.status in (SagaStatus.COMPLETED, SagaStatus.FAILED):
            raise ValueError(f"Cannot compensate saga {saga_id} in status {saga.status}")

        saga.mark_compensating(step=failed_step)
        return await self._repository.save(saga)

    # ---- Utility / Analytics ----

    async def is_saga_active(self, saga_id: UUID) -> bool:
        """Проверка, активна ли сага (не завершена и не провалена)."""
        saga = await self._repository.get(saga_id)
        if not saga:
            return False
        return saga.status in (SagaStatus.STARTED, SagaStatus.COMPENSATING)
