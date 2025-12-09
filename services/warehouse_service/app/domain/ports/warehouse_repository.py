from typing import Protocol, List, Optional
from uuid import UUID

from app.domain.entities import Warehouse


class WarehouseRepositoryPort(Protocol):
    """Порт для работы со складами в репозитории"""

    async def save(self, warehouse: Warehouse) -> Warehouse:
        """
        Сохранить склад (создание или обновление).
        """
        ...

    async def get(self, warehouse_id: UUID) -> Optional[Warehouse]:
        """
        Получить склад по ID.
        """
        ...

    async def get_all(self) -> List[Warehouse]:
        """
        Получить все склады.
        """
        ...

    async def delete(self, warehouse_id: UUID) -> None:
        """
        Удалить склад по ID.
        """
        ...
