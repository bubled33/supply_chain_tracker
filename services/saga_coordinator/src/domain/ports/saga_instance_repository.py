from typing import Protocol, Optional, List
from uuid import UUID

from src.domain.entities import SagaInstance


class SagaRepositoryPort(Protocol):
    async def save(self, saga: SagaInstance) -> SagaInstance:
        ...

    async def get(self, saga_id: UUID) -> Optional[SagaInstance]:
        ...

    async def get_by_shipment(self, shipment_id: UUID) -> Optional[SagaInstance]:
        ...

    async def list_active(self) -> List[SagaInstance]:
        ...

