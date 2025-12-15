from typing import List, Optional
from uuid import UUID

from src.domain.entities import InventoryRecord
from src.domain.entities.inventory_record import InventoryStatus
from src.domain.errors.inventory_record import InventoryRecordNotFoundError, InvalidInventoryStatusTransitionError
from src.domain.ports import InventoryRepositoryPort


class InventoryService:
    """Сервис для работы с записями инвентаря."""

    def __init__(self, repository: InventoryRepositoryPort):
        self._repository = repository

    async def create_record(self, record: InventoryRecord) -> InventoryRecord:
        """
        Создать новую запись инвентаря.
        """
        return await self._repository.save(record)

    async def get_record(self, record_id: UUID) -> Optional[InventoryRecord]:
        """
        Получить запись инвентаря по ID.
        """
        return await self._repository.get(record_id)

    async def list_records_by_shipment(self, shipment_id: UUID) -> List[InventoryRecord]:
        """
        Получить все записи инвентаря по shipment_id.
        """
        return await self._repository.list_by_shipment(shipment_id)

    async def delete_record(self, record_id: UUID) -> None:
        """
        Удалить запись инвентаря по ID.
        """
        existing = await self._repository.get(record_id)
        if existing is None:
            raise InventoryRecordNotFoundError(f"Inventory record {record_id} not found")

        await self._repository.delete(record_id)

    async def update_status(self, record_id: UUID, new_status: InventoryStatus) -> InventoryRecord:
        """
        Обновить статус записи инвентаря.
        """
        record = await self._repository.get(record_id)
        if record is None:
            raise InventoryRecordNotFoundError(f"Inventory record {record_id} not found")

        if record.status == InventoryStatus.SHIPPED and new_status != InventoryStatus.SHIPPED:
            raise InvalidInventoryStatusTransitionError(
                f"Cannot change status from {record.status} to {new_status}"
            )

        record.update_status(new_status)
        return await self._repository.save(record)
