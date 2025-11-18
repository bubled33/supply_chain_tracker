from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends
from starlette import status

from services.shipment_service.api.dto.item import (
    ItemDTO,
    ItemCreateDTO,
    ItemUpdateDTO,
)
from services.shipment_service.api.mappers import ItemMapper
from services.shipment_service.app.item import ItemService
from services.shipment_service.domain.entities.item import Item
from services.shipment_service.domain.errors import ItemNotFoundError

shipment_items_router = APIRouter(
    prefix="/shipments/{shipment_id}/items",
    tags=["items"]
)

items_router = APIRouter(
    prefix="/items",
    tags=["items"]
)


def get_item_service() -> ItemService:
    return ItemService()


@shipment_items_router.post(
    "",
    response_model=ItemDTO,
    status_code=status.HTTP_201_CREATED,
)
def create_item(
    shipment_id: UUID,
    dto: ItemCreateDTO,
    service: ItemService = Depends(get_item_service),
):
    """Создать item для конкретного shipment"""
    entity: Item = ItemMapper.create_dto_to_entity(dto, shipment_id)
    created: Item = service.create(entity)
    return ItemMapper.entity_to_dto(created)


@shipment_items_router.get(
    "",
    response_model=List[ItemDTO],
)
def list_shipment_items(
    shipment_id: UUID,
    service: ItemService = Depends(get_item_service),
):
    """Получить все items для конкретного shipment"""
    items = service.get_by_shipment(shipment_id)
    return [ItemMapper.entity_to_dto(i) for i in items]


@items_router.get(
    "/{item_id}",
    response_model=ItemDTO,
)
def get_item(
    item_id: UUID,
    service: ItemService = Depends(get_item_service),
):
    """Получить конкретный item по ID"""
    item = service.get(item_id)
    if item is None:
        raise ItemNotFoundError
    return ItemMapper.entity_to_dto(item)


@items_router.patch(
    "/{item_id}",
    response_model=ItemDTO,
)
def update_item(
    item_id: UUID,
    dto: ItemUpdateDTO,
    service: ItemService = Depends(get_item_service),
):
    """Обновить конкретный item"""
    item = service.get(item_id)
    if item is None:
        raise ItemNotFoundError

    updated_entity = ItemMapper.update_entity_from_dto(item, dto)
    saved = service.update(updated_entity)
    return ItemMapper.entity_to_dto(saved)


@items_router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_item(
    item_id: UUID,
    service: ItemService = Depends(get_item_service),
):
    """Удалить конкретный item"""
    item = service.get(item_id)
    if item is None:
        raise ItemNotFoundError

    service.delete(item_id)
