from typing import List, Optional
from uuid import UUID

from libs.value_objects.location import Location

from src.domain.entities import Warehouse
from src.domain.errors.warehouse import WarehouseNotFoundError
from src.domain.ports.warehouse_repository import WarehouseRepositoryPort


class WarehouseService:

    def __init__(self, repository: WarehouseRepositoryPort):
        self._repository = repository

    async def create(self, warehouse: Warehouse) -> Warehouse:
        return await self._repository.save(warehouse)

    async def get(self, warehouse_id: UUID) -> Optional[Warehouse]:
        return await self._repository.get(warehouse_id)

    async def get_all(self, limit: int = 50, offset: int = 0) -> List[Warehouse]:
        return await self._repository.get_all(limit=limit, offset=offset)

    async def update(self, warehouse: Warehouse) -> Warehouse:
        existing = await self._repository.get(warehouse.warehouse_id)
        if existing is None:
            raise WarehouseNotFoundError(f"Warehouse {warehouse.warehouse_id} not found")

        return await self._repository.save(warehouse)

    async def delete(self, warehouse_id: UUID) -> None:
        existing = await self._repository.get(warehouse_id)
        if existing is None:
            raise WarehouseNotFoundError(f"Warehouse {warehouse_id} not found")

        await self._repository.delete(warehouse_id)

    async def update_location(self, warehouse_id: UUID, new_location: Location) -> Warehouse:
        warehouse = await self._repository.get(warehouse_id)
        if warehouse is None:
            raise WarehouseNotFoundError(f"Warehouse {warehouse_id} not found")

        warehouse.update_location(new_location)
        return await self._repository.save(warehouse)
