from uuid import UUID
from typing import List
from datetime import datetime, timezone, date

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from libs.messaging.events import CourierAssigned, DomainEventConverter, DeliveryInTransit, DeliveryCompleted
from libs.messaging.ports import EventQueuePort
from src.api.deps.getters import (
    get_delivery_service,
    get_courier_service,
    get_event_queue
)

from src.api.dto.delivery import (
    DeliveryDTO,
    DeliveryCreateDTO,
    DeliveryUpdateDTO
)
from src.api.mappers.delivery import DeliveryMapper

from src.app.services.courier import CourierService
from src.app.services.delivery import DeliveryService
from src.domain.entities.delivery import Delivery, DeliveryStatus

delivery_router = APIRouter(prefix="/deliveries", tags=["deliveries"])


@delivery_router.post(
    "",
    response_model=DeliveryDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_delivery(
        dto: DeliveryCreateDTO,
        delivery_service: DeliveryService = Depends(get_delivery_service),
        courier_service: CourierService = Depends(get_courier_service),
        event_queue: EventQueuePort = Depends(get_event_queue),
):
    """
    Создать новую доставку (назначить курьера на груз).
    Публикует событие CourierAssigned.
    """
    courier = await courier_service.get(dto.courier_id)
    if not courier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Courier {dto.courier_id} not found"
        )

    entity: Delivery = DeliveryMapper.create_dto_to_entity(dto, courier)

    created: Delivery = await delivery_service.create(entity)

    domain_event = CourierAssigned(
        delivery_id=created.delivery_id,
        courier_id=created.courier.courier_id,
        shipment_id=created.shipment_id,
        estimated_delivery=datetime.combine(created.estimated_arrival,
                                            datetime.min.time()) if created.estimated_arrival else datetime.now(),
        # Приводим date к datetime, если нужно
        assigned_at=datetime.now(timezone.utc)
    )
    event = DomainEventConverter.to_event(domain_event)
    await event_queue.publish_event(event, topic="delivery-events")

    return DeliveryMapper.entity_to_dto(created)


@delivery_router.get(
    "/{delivery_id}",
    response_model=DeliveryDTO,
)
async def get_delivery(
        delivery_id: UUID,
        service: DeliveryService = Depends(get_delivery_service),
):
    """Получить доставку по ID"""
    delivery = await service.get(delivery_id)
    if delivery is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery {delivery_id} not found"
        )
    return DeliveryMapper.entity_to_dto(delivery)


@delivery_router.get(
    "",
    response_model=List[DeliveryDTO],
)
async def list_deliveries(
        service: DeliveryService = Depends(get_delivery_service),
):
    """Получить список всех доставок"""
    deliveries = await service.get_all()
    return [DeliveryMapper.entity_to_dto(d) for d in deliveries]


@delivery_router.patch(
    "/{delivery_id}",
    response_model=DeliveryDTO,
)
async def update_delivery(
        delivery_id: UUID,
        dto: DeliveryUpdateDTO,
        delivery_service: DeliveryService = Depends(get_delivery_service),
        courier_service: CourierService = Depends(get_courier_service),
        event_queue: EventQueuePort = Depends(get_event_queue),
):
    """
    Обновить данные доставки.
    Если меняется курьер -> CourierAssigned (новое назначение).
    """
    delivery = await delivery_service.get(delivery_id)
    if delivery is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery {delivery_id} not found"
        )

    new_courier = None
    is_courier_changed = False
    if dto.courier_id is not None and dto.courier_id != delivery.courier.courier_id:
        new_courier = await courier_service.get(dto.courier_id)
        if not new_courier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Courier {dto.courier_id} not found"
            )
        is_courier_changed = True

    updated_entity = DeliveryMapper.update_entity_from_dto(delivery, dto, new_courier)

    saved = await delivery_service.update(updated_entity)

    if is_courier_changed:
        domain_event = CourierAssigned(
            delivery_id=saved.delivery_id,
            courier_id=saved.courier.courier_id,
            shipment_id=saved.shipment_id,
            estimated_delivery=datetime.now(),
            assigned_at=datetime.now(timezone.utc)
        )
        event = DomainEventConverter.to_event(domain_event)
        await event_queue.publish_event(event, topic="delivery-events")

    return DeliveryMapper.entity_to_dto(saved)


@delivery_router.post(
    "/{delivery_id}/start",
    response_model=DeliveryDTO,
)
async def mark_delivery_in_transit(
        delivery_id: UUID,
        service: DeliveryService = Depends(get_delivery_service),
        event_queue: EventQueuePort = Depends(get_event_queue),
):
    """
    Перевести доставку в статус IN_TRANSIT.
    Публикует DeliveryInTransit.
    """
    delivery = await service.get(delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")

    await service.mark_as_in_transit(delivery_id)
    saved = await service.get(delivery_id)

    domain_event = DeliveryInTransit(
        delivery_id=saved.delivery_id,
        current_location="Warehouse",
        updated_at=datetime.now(timezone.utc)
    )
    await event_queue.publish_event(DomainEventConverter.to_event(domain_event), topic="delivery-events")

    return DeliveryMapper.entity_to_dto(saved)


@delivery_router.post(
    "/{delivery_id}/complete",
    response_model=DeliveryDTO,
)
async def complete_delivery(
        delivery_id: UUID,
        service: DeliveryService = Depends(get_delivery_service),
        event_queue: EventQueuePort = Depends(get_event_queue),
):
    """
    Завершить доставку (DELIVERED).
    Публикует DeliveryCompleted.
    """

    delivery = await service.get(delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")

    delivery.mark_delivered(actual_arrival=date.today())
    saved = await service.update(delivery)

    domain_event = DeliveryCompleted(
        delivery_id=saved.delivery_id,
        delivered_at=datetime.now(timezone.utc),
        recipient_name="Unknown",
        recipient_signature=None
    )
    await event_queue.publish_event(DomainEventConverter.to_event(domain_event), topic="delivery-events")

    return DeliveryMapper.entity_to_dto(saved)
