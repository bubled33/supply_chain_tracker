from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from src.api.deps.getters import get_courier_service
from src.api.dto.courier import (
    CourierDTO,
    CourierCreateDTO,
    CourierUpdateDTO
)
from src.api.mappers.courier import CourierMapper
from src.app.services.courier import CourierService

courier_router = APIRouter(prefix="/couriers", tags=["couriers"])


@courier_router.post(
    "",
    response_model=CourierDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_courier(
        dto: CourierCreateDTO,
        service: CourierService = Depends(get_courier_service),
):
    """
    Регистрация нового курьера.
    """
    entity = CourierMapper.create_dto_to_entity(dto)

    created = await service.create(entity)

    return CourierMapper.entity_to_dto(created)


@courier_router.get(
    "/{courier_id}",
    response_model=CourierDTO,
)
async def get_courier(
        courier_id: UUID,
        service: CourierService = Depends(get_courier_service),
):
    """Получить информацию о курьере по ID"""
    courier = await service.get(courier_id)
    if courier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Courier {courier_id} not found"
        )
    return CourierMapper.entity_to_dto(courier)


@courier_router.get(
    "",
    response_model=List[CourierDTO],
)
async def list_couriers(
        service: CourierService = Depends(get_courier_service),
):
    """Получить список всех курьеров"""
    couriers = await service.get_all()
    return [CourierMapper.entity_to_dto(c) for c in couriers]


@courier_router.patch(
    "/{courier_id}",
    response_model=CourierDTO,
)
async def update_courier(
        courier_id: UUID,
        dto: CourierUpdateDTO,
        service: CourierService = Depends(get_courier_service),
):
    """
    Обновить контактные данные или имя курьера.
    """
    courier = await service.get(courier_id)
    if courier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Courier {courier_id} not found"
        )

    updated_entity = CourierMapper.update_entity_from_dto(courier, dto)

    saved = await service.update(updated_entity)

    return CourierMapper.entity_to_dto(saved)


@courier_router.delete(
    "/{courier_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_courier(
        courier_id: UUID,
        service: CourierService = Depends(get_courier_service),
):
    """Удалить курьера из системы"""
    courier = await service.get(courier_id)
    if courier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Courier {courier_id} not found"
        )

    await service.delete(courier_id)
    return None
