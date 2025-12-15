from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from src.api.deps.getters import get_warehouse_service
from src.api.dto.warehouse import WarehouseDTO, WarehouseCreateDTO, WarehouseUpdateDTO
from src.api.mappers.warehouse import WarehouseMapper
from src.app.services.warehouse import WarehouseService

warehouse_router = APIRouter(
    prefix="/warehouses",
    tags=["warehouses"],
)

@warehouse_router.post(
    "",
    response_model=WarehouseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_warehouse(
    dto: WarehouseCreateDTO,
    service: WarehouseService = Depends(get_warehouse_service),
):
    entity = WarehouseMapper.create_dto_to_entity(dto)
    created = await service.create(entity)
    return WarehouseMapper.entity_to_dto(created)


@warehouse_router.get(
    "",
    response_model=List[WarehouseDTO],
)
async def list_warehouses(
    service: WarehouseService = Depends(get_warehouse_service),
):
    warehouses = await service.get_all()
    return [WarehouseMapper.entity_to_dto(w) for w in warehouses]


@warehouse_router.get(
    "/{warehouse_id}",
    response_model=WarehouseDTO,
)
async def get_warehouse(
    warehouse_id: UUID,
    service: WarehouseService = Depends(get_warehouse_service),
):
    warehouse = await service.get(warehouse_id)
    if warehouse is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Warehouse {warehouse_id} not found",
        )
    return WarehouseMapper.entity_to_dto(warehouse)


@warehouse_router.patch(
    "/{warehouse_id}",
    response_model=WarehouseDTO,
)
async def update_warehouse(
    warehouse_id: UUID,
    dto: WarehouseUpdateDTO,
    service: WarehouseService = Depends(get_warehouse_service),
):
    warehouse = await service.get(warehouse_id)
    if warehouse is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Warehouse {warehouse_id} not found",
        )

    updated_entity = WarehouseMapper.update_entity_from_dto(warehouse, dto)
    saved = await service.update(updated_entity)
    return WarehouseMapper.entity_to_dto(saved)


@warehouse_router.delete(
    "/{warehouse_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_warehouse(
    warehouse_id: UUID,
    service: WarehouseService = Depends(get_warehouse_service),
):
    warehouse = await service.get(warehouse_id)
    if warehouse is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Warehouse {warehouse_id} not found",
        )

    await service.delete(warehouse_id)
    return None
