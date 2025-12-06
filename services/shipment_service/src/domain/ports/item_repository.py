from typing import Protocol, List, Optional
from uuid import UUID

from src.domain.entities.item import Item


class ItemRepositoryPort(Protocol):
    """Порт для работы с Items в репозитории"""

    async def save(self, item: Item) -> Item:
        """
        Сохранить item (создание или обновление).

        Args:
            item: Сущность item для сохранения

        Returns:
            Сохраненный item с присвоенным ID
        """
        ...

    async def get(self, item_id: UUID) -> Optional[Item]:
        """
        Получить item по ID.

        Args:
            item_id: Уникальный идентификатор item

        Returns:
            Item или None, если не найден
        """
        ...

    async def get_by_shipment(self, shipment_id: UUID) -> List[Item]:
        """
        Получить все items для конкретного shipment.

        Args:
            shipment_id: ID shipment, для которого нужны items

        Returns:
            Список items для данного shipment
        """
        ...

    async def delete(self, item_id: UUID) -> None:
        """
        Удалить item по ID.

        Args:
            item_id: ID item для удаления

        Raises:
            ItemNotFoundError: Если item не найден
        """
        ...

    async def get_all(self) -> List[Item]:
        """
        Получить все items из всех shipments.

        Returns:
            Список всех items
        """
        ...
