from typing import Protocol, List, Optional
from uuid import UUID

from src.domain.entities.item import Item


class ItemRepositoryPort(Protocol):

    async def save(self, item: Item) -> Item:
        ...

    async def get(self, item_id: UUID) -> Optional[Item]:
        ...

    async def get_by_shipment(self, shipment_id: UUID) -> List[Item]:
        ...

    async def delete(self, item_id: UUID) -> None:
        ...

    async def get_all(self) -> List[Item]:
        ...
