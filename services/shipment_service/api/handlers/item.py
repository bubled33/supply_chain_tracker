from uuid import UUID
from typing import List
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from starlette import status

from services.shipment_service.api.deps.getters import (
    get_item_service,
    get_event_queue
)
from services.shipment_service.api.dto.item import (
    ItemDTO,
    ItemCreateDTO,
    ItemUpdateDTO,
)
from services.shipment_service.api.mappers import ItemMapper
from services.shipment_service.app.services.item import ItemService
from services.shipment_service.domain.entities.item import Item
from services.shipment_service.domain.errors import ItemNotFoundError
from libs.messaging.ports import EventQueuePort
from libs.messaging.events import (
    ShipmentUpdated,
    DomainEventConverter
)

shipment_items_router = APIRouter(
    prefix="/shipments/{shipment_id}/items",
    tags=["items"]
)

items_router = APIRouter(
    prefix="/items",
    tags=["items"]
)


@shipment_items_router.post(
    "",
    response_model=ItemDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_item(
        shipment_id: UUID,
        dto: ItemCreateDTO,
        service: ItemService = Depends(get_item_service),
        event_queue: EventQueuePort = Depends(get_event_queue),
):
    """Создать item для конкретного shipment и опубликовать событие"""
    entity: Item = ItemMapper.create_dto_to_entity(dto, shipment_id)
    created: Item = await service.create(entity)

    # Публикуем ShipmentUpdated (состав shipment изменился)
    domain_event = ShipmentUpdated(
        shipment_id=shipment_id,
        status="items_updated",
        updated_at=datetime.now(timezone.utc)
    )
    event = DomainEventConverter.to_event(domain_event)
    await event_queue.publish_event(event, topic="shipment-events")

    return ItemMapper.entity_to_dto(created)


@shipment_items_router.get(
    "",
    response_model=List[ItemDTO],
)
async def list_shipment_items(
        shipment_id: UUID,
        service: ItemService = Depends(get_item_service),
):
    """Получить все items для конкретного shipment"""
    items = await service.get_by_shipment(shipment_id)
    return [ItemMapper.entity_to_dto(i) for i in items]


@items_router.get(
    "/{item_id}",
    response_model=ItemDTO,
)
async def get_item(
        item_id: UUID,
        service: ItemService = Depends(get_item_service),
):
    """Получить конкретный item по ID"""
    item = await service.get(item_id)
    if item is None:
        raise ItemNotFoundError(f"Item {item_id} not found")
    return ItemMapper.entity_to_dto(item)


@items_router.patch(
    "/{item_id}",
    response_model=ItemDTO,
)
async def update_item(
        item_id: UUID,
        dto: ItemUpdateDTO,
        service: ItemService = Depends(get_item_service),
        event_queue: EventQueuePort = Depends(get_event_queue),
):
    """Обновить конкретный item и опубликовать событие"""
    item = await service.get(item_id)
    if item is None:
        raise ItemNotFoundError(f"Item {item_id} not found")

    updated_entity = ItemMapper.update_entity_from_dto(item, dto)
    saved = await service.update(updated_entity)

    # Публикуем ShipmentUpdated (состав shipment изменился)
    domain_event = ShipmentUpdated(
        shipment_id=saved.shipment_id,
        status="items_updated",
        updated_at=datetime.now(timezone.utc)
    )
    event = DomainEventConverter.to_event(domain_event)
    await event_queue.publish_event(event, topic="shipment-events")

    return ItemMapper.entity_to_dto(saved)


@items_router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_item(
        item_id: UUID,
        service: ItemService = Depends(get_item_service),
        event_queue: EventQueuePort = Depends(get_event_queue),
):
    """Удалить конкретный item и опубликовать событие"""
    item = await service.get(item_id)
    if item is None:
        raise ItemNotFoundError(f"Item {item_id} not found")

    shipment_id = item.shipment_id
    await service.delete(item_id)

    # Публикуем ShipmentUpdated (состав shipment изменился)
    domain_event = ShipmentUpdated(
        shipment_id=shipment_id,
        status="items_updated",
        updated_at=datetime.now(timezone.utc)
    )
    event = DomainEventConverter.to_event(domain_event)
    await event_queue.publish_event(event, topic="shipment-events")

    return None


# Дополнительные эндпоинты для бизнес-операций
@items_router.post(
    "/{item_id}/increase-quantity",
    response_model=ItemDTO,
)
async def increase_item_quantity(
        item_id: UUID,
        amount: int,
        service: ItemService = Depends(get_item_service),
        event_queue: EventQueuePort = Depends(get_event_queue),
):
    """Увеличить количество item"""
    item = await service.increase_quantity(item_id, amount)

    # Публикуем событие
    domain_event = ShipmentUpdated(
        shipment_id=item.shipment_id,
        status="items_updated",
        updated_at=datetime.now(timezone.utc)
    )
    event = DomainEventConverter.to_event(domain_event)
    await event_queue.publish_event(event, topic="shipment-events")

    return ItemMapper.entity_to_dto(item)


@items_router.post(
    "/{item_id}/decrease-quantity",
    response_model=ItemDTO,
)
async def decrease_item_quantity(
        item_id: UUID,
        amount: int,
        service: ItemService = Depends(get_item_service),
        event_queue: EventQueuePort = Depends(get_event_queue),
):
    """Уменьшить количество item"""
    item = await service.decrease_quantity(item_id, amount)

    # Публикуем событие
    domain_event = ShipmentUpdated(
        shipment_id=item.shipment_id,
        status="items_updated",
        updated_at=datetime.now(timezone.utc)
    )
    event = DomainEventConverter.to_event(domain_event)
    await event_queue.publish_event(event, topic="shipment-events")

    return ItemMapper.entity_to_dto(item)


@items_router.patch(
    "/{item_id}/weight",
    response_model=ItemDTO,
)
async def update_item_weight(
        item_id: UUID,
        new_weight: float,
        service: ItemService = Depends(get_item_service),
        event_queue: EventQueuePort = Depends(get_event_queue),
):
    """Обновить вес item"""
    item = await service.update_weight(item_id, new_weight)

    # Публикуем событие
    domain_event = ShipmentUpdated(
        shipment_id=item.shipment_id,
        status="items_updated",
        updated_at=datetime.now(timezone.utc)
    )
    event = DomainEventConverter.to_event(domain_event)
    await event_queue.publish_event(event, topic="shipment-events")

    return ItemMapper.entity_to_dto(item)


@shipment_items_router.get(
    "/total-weight",
    response_model=dict,
)
async def get_shipment_total_weight(
        shipment_id: UUID,
        service: ItemService = Depends(get_item_service),
):
    """Получить общий вес всех items в shipment"""
    total_weight = await service.calculate_total_weight(shipment_id)
    return {
        "shipment_id": str(shipment_id),
        "total_weight": total_weight,
        "unit": "kg"
    }


@shipment_items_router.get(
    "/count",
    response_model=dict,
)
async def get_shipment_items_count(
        shipment_id: UUID,
        service: ItemService = Depends(get_item_service),
):
    """Получить количество items в shipment"""
    count = await service.get_items_count(shipment_id)
    return {
        "shipment_id": str(shipment_id),
        "items_count": count
    }
