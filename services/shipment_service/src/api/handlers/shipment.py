from uuid import UUID
from typing import List
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from starlette import status

from src.api.deps.getters import (
    get_shipment_service,
    get_event_queue
)
from src.api.dto import ShipmentCreateDTO, ShipmentUpdateDTO
from src.api.dto.shipment import ShipmentDTO
from src.api.mappers import ShipmentMapper
from src.app.services.shipment import ShipmentService
from src.domain.entities.shipment import Shipment
from src.domain.errors import ShipmentNotFoundError
from libs.messaging.ports import EventQueuePort
from libs.messaging.events import (
    ShipmentCreated,
    ShipmentUpdated,
    ShipmentCancelled,
    DomainEventConverter
)

shipments_router = APIRouter(prefix="/shipments", tags=["shipments"])


@shipments_router.post(
    "",
    response_model=ShipmentDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_shipment(
        dto: ShipmentCreateDTO,
        service: ShipmentService = Depends(get_shipment_service),
        event_queue: EventQueuePort = Depends(get_event_queue),
):
    """Создать новую отправку и опубликовать событие ShipmentCreated"""
    # DTO -> Entity
    entity: Shipment = ShipmentMapper.create_dto_to_entity(dto)
    created: Shipment = await service.create(entity)

    # Публикуем событие ShipmentCreated
    domain_event = ShipmentCreated(
        shipment_id=created.shipment_id,
        origin=created.origin.city if hasattr(created.origin, 'city') else str(created.origin),
        destination=created.destination.city if hasattr(created.destination, 'city') else str(created.destination),
        items=[]  # Если items есть в dto: [item.to_dict() for item in dto.items]
    )
    event = DomainEventConverter.to_event(domain_event)
    await event_queue.publish_event(event, topic="shipment-events")

    return ShipmentMapper.entity_to_dto(created)


@shipments_router.get(
    "/{shipment_id}",
    response_model=ShipmentDTO,
)
async def get_shipment(
        shipment_id: UUID,
        service: ShipmentService = Depends(get_shipment_service),
):
    """Получить отправку по ID"""
    shipment = await service.get(shipment_id)
    if shipment is None:
        raise ShipmentNotFoundError(f"Shipment {shipment_id} not found")
    return ShipmentMapper.entity_to_dto(shipment)


@shipments_router.get(
    "",
    response_model=List[ShipmentDTO],
)
async def list_shipments(
        service: ShipmentService = Depends(get_shipment_service),
):
    """Получить список всех отправок"""
    shipments = await service.get_all()
    return [ShipmentMapper.entity_to_dto(s) for s in shipments]


@shipments_router.patch(
    "/{shipment_id}",
    response_model=ShipmentDTO,
)
async def update_shipment(
        shipment_id: UUID,
        dto: ShipmentUpdateDTO,
        service: ShipmentService = Depends(get_shipment_service),
        event_queue: EventQueuePort = Depends(get_event_queue),
):
    """Обновить отправку и опубликовать событие ShipmentUpdated"""
    shipment = await service.get(shipment_id)
    if shipment is None:
        raise ShipmentNotFoundError(f"Shipment {shipment_id} not found")

    # Обновляем entity
    updated_entity = ShipmentMapper.update_entity_from_dto(shipment, dto)
    saved = await service.update(updated_entity)

    # Публикуем событие ShipmentUpdated
    domain_event = ShipmentUpdated(
        shipment_id=saved.shipment_id,
        status=saved.status.value,
        updated_at=saved.updated_at.value
    )
    event = DomainEventConverter.to_event(domain_event)
    await event_queue.publish_event(event, topic="shipment-events")

    return ShipmentMapper.entity_to_dto(saved)


@shipments_router.delete(
    "/{shipment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_shipment(
        shipment_id: UUID,
        service: ShipmentService = Depends(get_shipment_service),
        event_queue: EventQueuePort = Depends(get_event_queue),
):
    """Удалить отправку и опубликовать событие ShipmentCancelled"""
    shipment = await service.get(shipment_id)
    if shipment is None:
        raise ShipmentNotFoundError(f"Shipment {shipment_id} not found")

    await service.delete(shipment_id)

    # Публикуем событие ShipmentCancelled
    domain_event = ShipmentCancelled(
        shipment_id=shipment_id,
        reason="User requested deletion",
        cancelled_at=datetime.now(timezone.utc)
    )
    event = DomainEventConverter.to_event(domain_event)
    await event_queue.publish_event(event, topic="shipment-events")

    return None


# Дополнительные эндпоинты для переходов между статусами
@shipments_router.post(
    "/{shipment_id}/receive",
    response_model=ShipmentDTO,
)
async def mark_shipment_received(
        shipment_id: UUID,
        service: ShipmentService = Depends(get_shipment_service),
        event_queue: EventQueuePort = Depends(get_event_queue),
):
    """Пометить отправку как полученную на складе (CREATED -> RECEIVED)"""
    shipment = await service.mark_as_received(shipment_id)

    # Публикуем событие ShipmentUpdated
    domain_event = ShipmentUpdated(
        shipment_id=shipment.shipment_id,
        status=shipment.status.value,
        updated_at=shipment.updated_at.value
    )
    event = DomainEventConverter.to_event(domain_event)
    await event_queue.publish_event(event, topic="shipment-events")

    return ShipmentMapper.entity_to_dto(shipment)


@shipments_router.post(
    "/{shipment_id}/ready-for-delivery",
    response_model=ShipmentDTO,
)
async def mark_shipment_ready(
        shipment_id: UUID,
        service: ShipmentService = Depends(get_shipment_service),
        event_queue: EventQueuePort = Depends(get_event_queue),
):
    """Пометить отправку как готовую к доставке (RECEIVED -> READY_FOR_DELIVERY)"""
    shipment = await service.mark_as_ready_for_delivery(shipment_id)

    domain_event = ShipmentUpdated(
        shipment_id=shipment.shipment_id,
        status=shipment.status.value,
        updated_at=shipment.updated_at.value
    )
    event = DomainEventConverter.to_event(domain_event)
    await event_queue.publish_event(event, topic="shipment-events")

    return ShipmentMapper.entity_to_dto(shipment)


@shipments_router.post(
    "/{shipment_id}/in-transit",
    response_model=ShipmentDTO,
)
async def mark_shipment_in_transit(
        shipment_id: UUID,
        service: ShipmentService = Depends(get_shipment_service),
        event_queue: EventQueuePort = Depends(get_event_queue),
):
    """Пометить отправку как находящуюся в пути (READY_FOR_DELIVERY -> IN_TRANSIT)"""
    shipment = await service.mark_as_in_transit(shipment_id)

    domain_event = ShipmentUpdated(
        shipment_id=shipment.shipment_id,
        status=shipment.status.value,
        updated_at=shipment.updated_at.value
    )
    event = DomainEventConverter.to_event(domain_event)
    await event_queue.publish_event(event, topic="shipment-events")

    return ShipmentMapper.entity_to_dto(shipment)


@shipments_router.post(
    "/{shipment_id}/delivered",
    response_model=ShipmentDTO,
)
async def mark_shipment_delivered(
        shipment_id: UUID,
        service: ShipmentService = Depends(get_shipment_service),
        event_queue: EventQueuePort = Depends(get_event_queue),
):
    """Пометить отправку как доставленную (IN_TRANSIT -> DELIVERED)"""
    from datetime import date

    shipment = await service.mark_as_delivered(shipment_id, arrival_date=date.today())

    domain_event = ShipmentUpdated(
        shipment_id=shipment.shipment_id,
        status=shipment.status.value,
        updated_at=shipment.updated_at.value
    )
    event = DomainEventConverter.to_event(domain_event)
    await event_queue.publish_event(event, topic="shipment-events")

    return ShipmentMapper.entity_to_dto(shipment)


@shipments_router.post(
    "/{shipment_id}/complete",
    response_model=ShipmentDTO,
)
async def mark_shipment_completed(
        shipment_id: UUID,
        service: ShipmentService = Depends(get_shipment_service),
        event_queue: EventQueuePort = Depends(get_event_queue),
):
    """Пометить отправку как завершённую (DELIVERED -> COMPLETED)"""
    shipment = await service.mark_as_completed(shipment_id)

    domain_event = ShipmentUpdated(
        shipment_id=shipment.shipment_id,
        status=shipment.status.value,
        updated_at=shipment.updated_at.value
    )
    event = DomainEventConverter.to_event(domain_event)
    await event_queue.publish_event(event, topic="shipment-events")

    return ShipmentMapper.entity_to_dto(shipment)


# Эндпоинты для запросов по статусам
@shipments_router.get(
    "/status/active",
    response_model=List[ShipmentDTO],
)
async def list_active_shipments(
        service: ShipmentService = Depends(get_shipment_service),
):
    """Получить все активные отправки"""
    shipments = await service.get_active_shipments()
    return [ShipmentMapper.entity_to_dto(s) for s in shipments]


@shipments_router.get(
    "/status/in-transit",
    response_model=List[ShipmentDTO],
)
async def list_in_transit_shipments(
        service: ShipmentService = Depends(get_shipment_service),
):
    """Получить отправки в пути"""
    shipments = await service.get_in_transit_shipments()
    return [ShipmentMapper.entity_to_dto(s) for s in shipments]
