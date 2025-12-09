from typing import Protocol, List, Optional
from uuid import UUID

from app.domain.entities import InventoryRecord


class InventoryRepositoryPort(Protocol):
    """Порт для работы с InventoryRecord в репозитории"""

    async def save(self, record: InventoryRecord) -> InventoryRecord:
        """
        Сохранить запись инвентаря (создание или обновление).
        """
        ...

    async def get(self, record_id: UUID) -> Optional[InventoryRecord]:
        """
        Получить запись инвентаря по ID.
        """
        ...

    async def list_by_shipment(self, shipment_id: UUID) -> List[InventoryRecord]:
        """
        Получить записи инвентаря по ID отправления.
        """
        ...

    async def delete(self, record_id: UUID) -> None:
        """
        Удалить запись инвентаря по ID.
        """
        ...
