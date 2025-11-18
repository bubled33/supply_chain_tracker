from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends
from starlette import status

from services.shipment_service.api.dto import ShipmentCreateDTO, ShipmentUpdateDTO
from services.shipment_service.api.dto.item import (
    ItemDTO,
)
from services.shipment_service.api.mappers import ShipmentMapper
from services.shipment_service.app.shipment import ShipmentService
from services.shipment_service.domain.entities import Shipment
from services.shipment_service.domain.errors import ItemNotFoundError

shipments_router = APIRouter(prefix="/shipments", tags=["shipments"])


def get_shipment_service() -> ShipmentService:
    return ShipmentService()


@shipments_router.post(
    "",
    response_model=ItemDTO,
    status_code=status.HTTP_201_CREATED,
)
def create_item(
    dto: ShipmentCreateDTO,
    service: ShipmentService = Depends(get_shipment_service),
):
    # DTO -> Entity
    entity: Shipment = ShipmentMapper.create_dto_to_entity(dto)
    created: Shipment = service.create(entity)
    return ShipmentMapper.entity_to_dto(created)


@shipments_router.get(
    "",
    response_model=ItemDTO,
)
def get_item(
    item_id: UUID,
    service: ShipmentService = Depends(get_shipment_service),
):
    item = service.get(item_id)
    if item is None:
        raise ItemNotFoundError
    return ShipmentMapper.entity_to_dto(item)


@shipments_router.get(
    "",
    response_model=List[ItemDTO],
)
def list_items(
    service: ShipmentService = Depends(get_shipment_service),
):
    shipments = service.get_all()
    return [ShipmentMapper.entity_to_dto(s) for s in shipments]


@shipments_router.patch(
    "/{shipment_id}",
    response_model=ItemDTO,
)
def update_item(
    shipment_id: UUID,
    dto: ShipmentUpdateDTO,
    service: ShipmentService = Depends(get_shipment_service),
):
    item = service.get(shipment_id)
    if item is None:
        raise ItemNotFoundError

    updated_entity = ShipmentMapper.update_entity_from_dto(item, dto)
    saved = service.update(updated_entity)
    return ShipmentMapper.entity_to_dto(saved)


@shipments_router.delete(
    "/{shipment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_item(
    shipment_id: UUID,
    service: ShipmentService = Depends(get_shipment_service),
):
    shipment = service.get(shipment_id)
    if shipment is None:
        raise ItemNotFoundError

    service.delete(shipment_id)
    return None
