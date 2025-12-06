from uuid import UUID
from typing import List, Optional

from src.domain.entities.item import Item
from src.domain.ports import ItemRepositoryPort
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.weight import Weight
from src.domain.errors import ItemNotFoundError


class ItemService:
    """Сервис для работы с Items"""

    def __init__(
        self,
        repository: ItemRepositoryPort,
    ):
        self._repository = repository

    # ---- CRUD ----

    async def create(self, item: Item) -> Item:
        """
        Создать новый item.

        Args:
            item: Item entity для создания

        Returns:
            Созданный item с присвоенным ID
        """
        return await self._repository.save(item)

    async def get(self, item_id: UUID) -> Optional[Item]:
        """
        Получить item по ID.

        Args:
            item_id: ID item

        Returns:
            Item или None, если не найден
        """
        return await self._repository.get(item_id)

    async def update(self, item: Item) -> Item:
        """
        Обновить существующий item.

        Args:
            item: Item entity с обновлёнными данными

        Returns:
            Обновлённый item

        Raises:
            ItemNotFoundError: Если item не найден
        """
        existing = await self._repository.get(item.item_id)
        if existing is None:
            raise ItemNotFoundError(f"Item {item.item_id} not found")

        return await self._repository.save(item)

    async def delete(self, item_id: UUID) -> None:
        """
        Удалить item по ID.

        Args:
            item_id: ID item для удаления

        Raises:
            ItemNotFoundError: Если item не найден
        """
        await self._repository.delete(item_id)

    async def get_all(self) -> List[Item]:
        """
        Получить все items.

        Returns:
            Список всех items
        """
        return await self._repository.get_all()

    async def get_by_shipment(self, shipment_id: UUID) -> List[Item]:
        """
        Получить все items для конкретного shipment.

        Args:
            shipment_id: ID shipment

        Returns:
            Список items для данного shipment
        """
        return await self._repository.get_by_shipment(shipment_id)

    # ---- Бизнес методы ----

    async def increase_quantity(self, item_id: UUID, amount: int) -> Item:
        """
        Увеличить количество item.

        Args:
            item_id: ID item
            amount: На сколько увеличить количество

        Returns:
            Обновлённый item

        Raises:
            ItemNotFoundError: Если item не найден
        """
        item = await self._repository.get(item_id)
        if item is None:
            raise ItemNotFoundError(f"Item {item_id} not found")

        # Увеличиваем количество через value object
        new_quantity = Quantity(item.quantity.value + amount)
        item.quantity = new_quantity

        return await self._repository.save(item)

    async def decrease_quantity(self, item_id: UUID, amount: int) -> Item:
        """
        Уменьшить количество item.

        Args:
            item_id: ID item
            amount: На сколько уменьшить количество

        Returns:
            Обновлённый item

        Raises:
            ItemNotFoundError: Если item не найден
            ValueError: Если итоговое количество будет отрицательным
        """
        item = await self._repository.get(item_id)
        if item is None:
            raise ItemNotFoundError(f"Item {item_id} not found")

        new_value = item.quantity.value - amount
        if new_value < 0:
            raise ValueError(
                f"Cannot decrease quantity: result would be negative "
                f"(current: {item.quantity.value}, decrease by: {amount})"
            )

        # Уменьшаем количество через value object
        new_quantity = Quantity(new_value)
        item.quantity = new_quantity

        return await self._repository.save(item)

    async def update_weight(self, item_id: UUID, new_weight: float) -> Item:
        """
        Обновить вес item.

        Args:
            item_id: ID item
            new_weight: Новый вес в кг

        Returns:
            Обновлённый item

        Raises:
            ItemNotFoundError: Если item не найден
        """
        item = await self._repository.get(item_id)
        if item is None:
            raise ItemNotFoundError(f"Item {item_id} not found")

        # Обновляем вес через value object
        item.weight = Weight(new_weight)

        return await self._repository.save(item)

    async def calculate_total_weight(self, shipment_id: UUID) -> float:
        """
        Рассчитать общий вес всех items в shipment.

        Args:
            shipment_id: ID shipment

        Returns:
            Общий вес в кг
        """
        items = await self._repository.get_by_shipment(shipment_id)
        return sum(item.weight.value * item.quantity.value for item in items)

    async def get_items_count(self, shipment_id: UUID) -> int:
        """
        Получить количество items в shipment.

        Args:
            shipment_id: ID shipment

        Returns:
            Количество items
        """
        items = await self._repository.get_by_shipment(shipment_id)
        return len(items)
