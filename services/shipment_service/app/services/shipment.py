from uuid import UUID
from typing import List, Optional
from datetime import date

from services.shipment_service.domain.entities.shipment import Shipment
from services.shipment_service.domain.ports import ShipmentRepositoryPort
from services.shipment_service.domain.value_objects.shipment_status import ShipmentStatus
from services.shipment_service.domain.errors import ShipmentNotFoundError


class ShipmentService:
    """Сервис для работы с Shipments"""

    def __init__(
            self,
            repository: ShipmentRepositoryPort,
    ):
        self._repository = repository

    # ---- CRUD ----

    async def create(self, shipment: Shipment) -> Shipment:
        """
        Создать новую отправку.

        Args:
            shipment: Shipment entity для создания

        Returns:
            Созданная отправка с присвоенным ID
        """
        return await self._repository.save(shipment)

    async def get(self, shipment_id: UUID) -> Optional[Shipment]:
        """
        Получить отправку по ID.

        Args:
            shipment_id: ID отправки

        Returns:
            Shipment или None, если не найдена
        """
        return await self._repository.get(shipment_id)

    async def update(self, shipment: Shipment) -> Shipment:
        """
        Обновить существующую отправку.

        Args:
            shipment: Shipment entity с обновлёнными данными

        Returns:
            Обновлённая отправка

        Raises:
            ShipmentNotFoundError: Если отправка не найдена
        """
        existing = await self._repository.get(shipment.shipment_id)
        if existing is None:
            raise ShipmentNotFoundError(f"Shipment {shipment.shipment_id} not found")

        return await self._repository.save(shipment)

    async def delete(self, shipment_id: UUID) -> None:
        """
        Удалить отправку по ID.

        Args:
            shipment_id: ID отправки для удаления

        Raises:
            ShipmentNotFoundError: Если отправка не найдена
        """
        await self._repository.delete(shipment_id)

    async def get_all(self) -> List[Shipment]:
        """
        Получить все отправки.

        Returns:
            Список всех отправок
        """
        return await self._repository.get_all()

    # ---- Бизнес методы - переходы между статусами ----

    async def update_status(
            self,
            shipment_id: UUID,
            new_status: ShipmentStatus
    ) -> Shipment:
        """
        Обновить статус отправки.

        Args:
            shipment_id: ID отправки
            new_status: Новый статус

        Returns:
            Обновлённая отправка

        Raises:
            ShipmentNotFoundError: Если отправка не найдена
        """
        shipment = await self._repository.get(shipment_id)
        if shipment is None:
            raise ShipmentNotFoundError(f"Shipment {shipment_id} not found")

        shipment.update_status(new_status)
        return await self._repository.save(shipment)

    async def mark_as_received(self, shipment_id: UUID) -> Shipment:
        """
        Пометить отправку как полученную на складе.
        CREATED -> RECEIVED

        Args:
            shipment_id: ID отправки

        Returns:
            Обновлённая отправка
        """
        return await self.update_status(shipment_id, ShipmentStatus.RECEIVED)

    async def mark_as_ready_for_delivery(self, shipment_id: UUID) -> Shipment:
        """
        Пометить отправку как готовую к доставке.
        RECEIVED -> READY_FOR_DELIVERY

        Args:
            shipment_id: ID отправки

        Returns:
            Обновлённая отправка
        """
        return await self.update_status(shipment_id, ShipmentStatus.READY_FOR_DELIVERY)

    async def mark_as_in_transit(self, shipment_id: UUID) -> Shipment:
        """
        Пометить отправку как находящуюся в пути.
        READY_FOR_DELIVERY -> IN_TRANSIT

        Args:
            shipment_id: ID отправки

        Returns:
            Обновлённая отправка
        """
        return await self.update_status(shipment_id, ShipmentStatus.IN_TRANSIT)

    async def mark_as_delivered(
            self,
            shipment_id: UUID,
            arrival_date: date
    ) -> Shipment:
        """
        Пометить отправку как доставленную.
        IN_TRANSIT -> DELIVERED

        Args:
            shipment_id: ID отправки
            arrival_date: Дата доставки

        Returns:
            Обновлённая отправка

        Raises:
            ShipmentNotFoundError: Если отправка не найдена
        """
        shipment = await self._repository.get(shipment_id)
        if shipment is None:
            raise ShipmentNotFoundError(f"Shipment {shipment_id} not found")

        # Используем метод entity для обновления статуса и даты
        shipment.mark_delivered(arrival_date)
        return await self._repository.save(shipment)

    async def mark_as_completed(self, shipment_id: UUID) -> Shipment:
        """
        Пометить отправку как завершённую (записано в блокчейн).
        DELIVERED -> COMPLETED

        Args:
            shipment_id: ID отправки

        Returns:
            Обновлённая отправка
        """
        return await self.update_status(shipment_id, ShipmentStatus.COMPLETED)

    # ---- Запросы по статусам ----

    async def get_by_status(self, status: ShipmentStatus) -> List[Shipment]:
        """
        Получить все отправки с определённым статусом.

        Args:
            status: Статус для фильтрации

        Returns:
            Список отправок с указанным статусом
        """
        all_shipments = await self._repository.get_all()
        return [s for s in all_shipments if s.status == status]

    async def get_created_shipments(self) -> List[Shipment]:
        """
        Получить отправки со статусом CREATED.

        Returns:
            Список созданных отправок
        """
        return await self.get_by_status(ShipmentStatus.CREATED)

    async def get_received_shipments(self) -> List[Shipment]:
        """
        Получить отправки, полученные на складе.

        Returns:
            Список отправок со статусом RECEIVED
        """
        return await self.get_by_status(ShipmentStatus.RECEIVED)

    async def get_ready_for_delivery_shipments(self) -> List[Shipment]:
        """
        Получить отправки, готовые к доставке.

        Returns:
            Список отправок со статусом READY_FOR_DELIVERY
        """
        return await self.get_by_status(ShipmentStatus.READY_FOR_DELIVERY)

    async def get_in_transit_shipments(self) -> List[Shipment]:
        """
        Получить отправки в пути.

        Returns:
            Список отправок со статусом IN_TRANSIT
        """
        return await self.get_by_status(ShipmentStatus.IN_TRANSIT)

    async def get_delivered_shipments(self) -> List[Shipment]:
        """
        Получить доставленные отправки.

        Returns:
            Список отправок со статусом DELIVERED
        """
        return await self.get_by_status(ShipmentStatus.DELIVERED)

    async def get_completed_shipments(self) -> List[Shipment]:
        """
        Получить завершённые отправки (записаны в блокчейн).

        Returns:
            Список отправок со статусом COMPLETED
        """
        return await self.get_by_status(ShipmentStatus.COMPLETED)

    async def get_active_shipments(self) -> List[Shipment]:
        """
        Получить все активные отправки (не завершённые).

        Returns:
            Список активных отправок (статусы CREATED - DELIVERED)
        """
        all_shipments = await self._repository.get_all()
        return [
            s for s in all_shipments
            if s.status != ShipmentStatus.COMPLETED
        ]

    async def get_pending_shipments(self) -> List[Shipment]:
        """
        Получить отправки, ожидающие обработки на складе.

        Returns:
            Список отправок со статусами CREATED или RECEIVED
        """
        all_shipments = await self._repository.get_all()
        return [
            s for s in all_shipments
            if s.status in [ShipmentStatus.CREATED, ShipmentStatus.RECEIVED]
        ]

    # ---- Вспомогательные методы ----

    async def can_transition_to(
            self,
            shipment_id: UUID,
            target_status: ShipmentStatus
    ) -> bool:
        """
        Проверить, можно ли перевести отправку в указанный статус.

        Args:
            shipment_id: ID отправки
            target_status: Целевой статус

        Returns:
            True, если переход возможен

        Raises:
            ShipmentNotFoundError: Если отправка не найдена
        """
        shipment = await self._repository.get(shipment_id)
        if shipment is None:
            raise ShipmentNotFoundError(f"Shipment {shipment_id} not found")

        # Определяем допустимые переходы
        valid_transitions = {
            ShipmentStatus.CREATED: [ShipmentStatus.RECEIVED],
            ShipmentStatus.RECEIVED: [ShipmentStatus.READY_FOR_DELIVERY],
            ShipmentStatus.READY_FOR_DELIVERY: [ShipmentStatus.IN_TRANSIT],
            ShipmentStatus.IN_TRANSIT: [ShipmentStatus.DELIVERED],
            ShipmentStatus.DELIVERED: [ShipmentStatus.COMPLETED],
            ShipmentStatus.COMPLETED: [],  # Финальный статус
        }

        current_status = shipment.status
        allowed_statuses = valid_transitions.get(current_status, [])

        return target_status in allowed_statuses

    async def get_shipment_lifecycle(self, shipment_id: UUID) -> dict:
        """
        Получить информацию о жизненном цикле отправки.

        Args:
            shipment_id: ID отправки

        Returns:
            Словарь с информацией о статусе и датах

        Raises:
            ShipmentNotFoundError: Если отправка не найдена
        """
        shipment = await self._repository.get(shipment_id)
        if shipment is None:
            raise ShipmentNotFoundError(f"Shipment {shipment_id} not found")

        return {
            "shipment_id": str(shipment.shipment_id),
            "current_status": shipment.status.value,
            "created_at": shipment.created_at.value.isoformat(),
            "updated_at": shipment.updated_at.value.isoformat(),
            "departure_date": str(shipment.departure_date),
            "arrival_date": str(shipment.arrival_date) if shipment.arrival_date else None,
            "is_completed": shipment.status == ShipmentStatus.COMPLETED,
            "is_in_progress": shipment.status in [
                ShipmentStatus.READY_FOR_DELIVERY,
                ShipmentStatus.IN_TRANSIT
            ],
        }
