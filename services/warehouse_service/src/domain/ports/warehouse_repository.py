from typing import Protocol, List, Optional
from uuid import UUID

from src.domain.entities import Warehouse


class WarehouseRepositoryPort(Protocol):

    async def save(self, warehouse: Warehouse) -> Warehouse:
        ...

    async def get(self, warehouse_id: UUID) -> Optional[Warehouse]:
        ...

    async def get_all(self, limit: int = 50, offset: int = 0) -> List[Warehouse]:
        ...

    async def delete(self, warehouse_id: UUID) -> None:
        ...
