from typing import Protocol, List, Optional
from uuid import UUID

from src.domain.entities import InventoryRecord


class InventoryRepositoryPort(Protocol):

    async def save(self, record: InventoryRecord) -> InventoryRecord:
        ...

    async def get(self, record_id: UUID) -> Optional[InventoryRecord]:
        ...

    async def list_by_shipment(self, shipment_id: UUID) -> List[InventoryRecord]:
        ...

    async def delete(self, record_id: UUID) -> None:
        ...
