
from uuid import UUID
from typing import List, Optional

from src.domain.entities.saga_instance import SagaInstance, SagaStatus
from src.domain.ports.saga_instance_repository import SagaRepositoryPort


class SagaService:

    def __init__(
            self,
            repository: SagaRepositoryPort,
    ):
        self._repository = repository


    async def create(self, saga: SagaInstance) -> SagaInstance:
        return await self._repository.save(saga)

    async def get(self, saga_id: UUID) -> Optional[SagaInstance]:
        return await self._repository.get(saga_id)

    async def get_by_shipment(self, shipment_id: UUID) -> Optional[SagaInstance]:
        return await self._repository.get_by_shipment(shipment_id)

    async def list_active_sagas(self) -> List[SagaInstance]:
        return await self._repository.list_active()


    async def update_context(self, saga_id: UUID, **kwargs) -> SagaInstance:
        saga = await self._repository.get(saga_id)
        if not saga:
            raise ValueError(f"Saga {saga_id} not found")

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
        saga = await self._repository.get(saga_id)
        if not saga:
            raise ValueError(f"Saga {saga_id} not found")

        if saga.status != SagaStatus.STARTED:
            return saga

        saga.mark_completed()
        return await self._repository.save(saga)

    async def fail_saga(self, saga_id: UUID, step: str, error_message: str) -> SagaInstance:
        saga = await self._repository.get(saga_id)
        if not saga:
            raise ValueError(f"Saga {saga_id} not found")

        saga.mark_failed(step=step, error=error_message)
        return await self._repository.save(saga)

    async def trigger_compensation(self, saga_id: UUID, failed_step: str) -> SagaInstance:
        saga = await self._repository.get(saga_id)
        if not saga:
            raise ValueError(f"Saga {saga_id} not found")

        if saga.status in (SagaStatus.COMPLETED, SagaStatus.FAILED):
            raise ValueError(f"Cannot compensate saga {saga_id} in status {saga.status}")

        saga.mark_compensating(step=failed_step)
        return await self._repository.save(saga)


    async def is_saga_active(self, saga_id: UUID) -> bool:
        saga = await self._repository.get(saga_id)
        if not saga:
            return False
        return saga.status in (SagaStatus.STARTED, SagaStatus.COMPENSATING)
