from abc import ABC, abstractmethod
from uuid import UUID

from services.warehouse_service.app.domain.entities.inventory_record import InventoryRecord


class InventoryRepositoryPort(ABC):
    @abstractmethod
    def add_record(self, record: InventoryRecord) -> InventoryRecord:
        pass

    @abstractmethod
    def get_record(self, record_id: UUID) -> InventoryRecord:
        pass

    @abstractmethod
    def update_record(self, record: InventoryRecord) -> InventoryRecord:
        pass

    @abstractmethod
    def list_records_by_shipment(self, shipment_id: UUID) -> list[InventoryRecord]:
        pass
