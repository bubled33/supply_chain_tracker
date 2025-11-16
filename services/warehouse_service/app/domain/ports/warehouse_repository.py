from abc import ABC, abstractmethod
from uuid import UUID

from services.warehouse_service.app.domain.entities import Warehouse


class WarehouseRepositoryPort(ABC):
    @abstractmethod
    def add_warehouse(self, warehouse: Warehouse) -> Warehouse:
        pass

    @abstractmethod
    def get_warehouse(self, warehouse_id: UUID) -> Warehouse:
        pass

    @abstractmethod
    def update_warehouse(self, warehouse: Warehouse) -> Warehouse:
        pass

    @abstractmethod
    def list_warehouses(self) -> list[Warehouse]:
        pass
