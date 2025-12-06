from uuid import UUID
from typing import List
from datetime import datetime, timezone, date

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from libs.messaging.events import CourierAssigned, DomainEventConverter, DeliveryInTransit, DeliveryCompleted
# Импорт портов и конвертера событий
from libs.messaging.ports import EventQueuePort
# Импорт зависимостей (getters)
from src.api.deps.getters import (
    get_delivery_service,
    get_courier_service,
    get_event_queue
)

# Импорт DTO
from src.api.dto.delivery import (
    DeliveryDTO,
    DeliveryCreateDTO,
    DeliveryUpdateDTO
)
from src.api.mappers.delivery import DeliveryMapper

# Импорт Сервисов и Сущностей
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
    # 1. Получаем объект курьера
    courier = await courier_service.get(dto.courier_id)
    if not courier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Courier {dto.courier_id} not found"
        )

    # 2. Маппинг DTO -> Entity
    entity: Delivery = DeliveryMapper.create_dto_to_entity(dto, courier)

    # 3. Сохранение через сервис
    created: Delivery = await create(entity)

    # 4. Публикация события CourierAssigned
    # Используем datetime.now(timezone.utc) для assigned_at
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
    # 1. Получаем существующую доставку
    delivery = await get(delivery_id)
    if delivery is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery {delivery_id} not found"
        )

    # 2. Если меняется курьер, нужно найти нового
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

    # 3. Обновляем Entity
    updated_entity = DeliveryMapper.update_entity_from_dto(delivery, dto, new_courier)

    # 4. Сохраняем
    saved = await update(updated_entity)

    # 5. Публикуем событие
    # Если сменился курьер - логично кинуть CourierAssigned
    if is_courier_changed:
        domain_event = CourierAssigned(
            delivery_id=saved.delivery_id,
            courier_id=saved.courier.courier_id,
            shipment_id=saved.shipment_id,
            estimated_delivery=datetime.now(),  # Упрощение, берем текущее
            assigned_at=datetime.now(timezone.utc)
        )
        event = DomainEventConverter.to_event(domain_event)
        await event_queue.publish_event(event, topic="delivery-events")

    # Если просто обновился статус или время, можно не кидать событие,
    # либо добавить Generic событие "DeliveryDetailsUpdated", но в вашем списке его нет.
    # Оставим пока публикацию только при смене курьера или используем специфичные эндпоинты ниже.

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

    # Бизнес-логика
    await service.mark_as_in_transit(delivery_id)  # Лучше использовать метод сервиса
    # Или если через update:
    # delivery.update_status(DeliveryStatus.IN_TRANSIT)
    # saved = await service.update(delivery)
    saved = await service.get(delivery_id)  # Получаем обновленную версию

    # Событие DeliveryInTransit
    domain_event = DeliveryInTransit(
        delivery_id=saved.delivery_id,
        current_location="Warehouse",  # Заглушка, или передавать в body запроса
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

    # Бизнес-логика
    # await service.mark_as_delivered(delivery_id, date.today())
    # Для примера используем прямое обновление если метода нет в интерфейсе, но лучше через сервис
    delivery.mark_delivered(actual_arrival=date.today())
    saved = await service.update(delivery)

    # Событие DeliveryCompleted
    domain_event = DeliveryCompleted(
        delivery_id=saved.delivery_id,
        delivered_at=datetime.now(timezone.utc),
        recipient_name="Unknown",  # Можно брать из request body
        recipient_signature=None
    )
    await event_queue.publish_event(DomainEventConverter.to_event(domain_event), topic="delivery-events")

    return DeliveryMapper.entity_to_dto(saved)
