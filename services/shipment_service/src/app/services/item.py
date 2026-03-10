from uuid import UUID
from typing import List, Optional

from src.domain.entities.item import Item
from src.domain.ports import ItemRepositoryPort
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.weight import Weight
from src.domain.errors import ItemNotFoundError


class ItemService:

    def __init__(
        self,
        repository: ItemRepositoryPort,
    ):
        self._repository = repository


    async def create(self, item: Item) -> Item:
        return await self._repository.save(item)

    async def get(self, item_id: UUID) -> Optional[Item]:
        return await self._repository.get(item_id)

    async def update(self, item: Item) -> Item:
        existing = await self._repository.get(item.item_id)
        if existing is None:
            raise ItemNotFoundError(f"Item {item.item_id} not found")

        return await self._repository.save(item)

    async def delete(self, item_id: UUID) -> None:
        await self._repository.delete(item_id)

    async def get_all(self) -> List[Item]:
        return await self._repository.get_all()

    async def get_by_shipment(self, shipment_id: UUID) -> List[Item]:
        return await self._repository.get_by_shipment(shipment_id)


    async def increase_quantity(self, item_id: UUID, amount: int) -> Item:
        item = await self._repository.get(item_id)
        if item is None:
            raise ItemNotFoundError(f"Item {item_id} not found")

        new_quantity = Quantity(item.quantity.value + amount)
        item.quantity = new_quantity

        return await self._repository.save(item)

    async def decrease_quantity(self, item_id: UUID, amount: int) -> Item:
        item = await self._repository.get(item_id)
        if item is None:
            raise ItemNotFoundError(f"Item {item_id} not found")

        new_value = item.quantity.value - amount
        if new_value < 0:
            raise ValueError(
                f"Cannot decrease quantity: result would be negative "
                f"(current: {item.quantity.value}, decrease by: {amount})"
            )

        new_quantity = Quantity(new_value)
        item.quantity = new_quantity

        return await self._repository.save(item)

    async def update_weight(self, item_id: UUID, new_weight: float) -> Item:
        item = await self._repository.get(item_id)
        if item is None:
            raise ItemNotFoundError(f"Item {item_id} not found")

        item.weight = Weight(new_weight)

        return await self._repository.save(item)

    async def calculate_total_weight(self, shipment_id: UUID) -> float:
        items = await self._repository.get_by_shipment(shipment_id)
        return sum(item.weight.value * item.quantity.value for item in items)

    async def get_items_count(self, shipment_id: UUID) -> int:
        items = await self._repository.get_by_shipment(shipment_id)
        return len(items)
