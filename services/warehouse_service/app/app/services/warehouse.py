from typing import List, Optional
from uuid import UUID

from libs.value_objects.location import Location

from app.domain.entities import Warehouse
from app.domain.errors.warehouse import WarehouseNotFoundError
from app.domain.ports.warehouse_repository import WarehouseRepositoryPort


class WarehouseService:
    """Сервис для работы со складами."""

    def __init__(self, repository: WarehouseRepositoryPort):
        self._repository = repository

    async def create(self, warehouse: Warehouse) -> Warehouse:
        """
        Создать новый склад.
        """
        return await self._repository.save(warehouse)

    async def get(self, warehouse_id: UUID) -> Optional[Warehouse]:
        """
        Получить склад по ID.
        """
        return await self._repository.get(warehouse_id)

    async def get_all(self) -> List[Warehouse]:
        """
        Получить все склады.
        """
        return await self._repository.get_all()

    async def update(self, warehouse: Warehouse) -> Warehouse:
        """
        Обновить существующий склад.
        """
        existing = await self._repository.get(warehouse.warehouse_id)
        if existing is None:
            raise WarehouseNotFoundError(f"Warehouse {warehouse.warehouse_id} not found")

        return await self._repository.save(warehouse)

    async def delete(self, warehouse_id: UUID) -> None:
        """
        Удалить склад по ID.
        """
        existing = await self._repository.get(warehouse_id)
        if existing is None:
            raise WarehouseNotFoundError(f"Warehouse {warehouse_id} not found")

        await self._repository.delete(warehouse_id)

    async def update_location(self, warehouse_id: UUID, new_location: Location) -> Warehouse:
        """
        Обновить локацию склада.
        """
        warehouse = await self._repository.get(warehouse_id)
        if warehouse is None:
            raise WarehouseNotFoundError(f"Warehouse {warehouse_id} not found")

        warehouse.update_location(new_location)
        return await self._repository.save(warehouse)
