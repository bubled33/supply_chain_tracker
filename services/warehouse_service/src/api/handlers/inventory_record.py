from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from libs.messaging.events import InventoryReserved, DomainEventConverter, InventoryUpdated, InventoryReleased
from libs.messaging.ports import EventQueuePort
from starlette import status

from src.api.deps.getters import get_event_queue, get_inventory_service
from src.api.dto.inventory_record import InventoryRecordDTO, InventoryRecordCreateDTO, InventoryRecordUpdateDTO
from src.api.mappers.inventory_record import InventoryRecordMapper
from src.app.services.inventory_record import InventoryService
from src.domain.entities import InventoryRecord

inventory_router = APIRouter(
    prefix="/warehouses/{warehouse_id}/inventory",
    tags=["inventory"],
)

@inventory_router.post(
    "",
    response_model=InventoryRecordDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_inventory_record(
    warehouse_id: UUID,
    dto: InventoryRecordCreateDTO,
    service: InventoryService = Depends(get_inventory_service),
    event_queue: EventQueuePort = Depends(get_event_queue),
):
    """
    Создать запись инвентаря для склада и опубликовать InventoryReserved.
    shipment_id приходит в dto.
    """
    dto.warehouse_id = warehouse_id

    entity: InventoryRecord = InventoryRecordMapper.create_dto_to_entity(dto)
    created: InventoryRecord = await service.create_record(entity)

    domain_event = InventoryReserved(
        warehouse_id=warehouse_id,
        shipment_id=created.shipment_id,
        items=[],  # либо собрать структуру items
        reserved_at=datetime.now(timezone.utc),
    )
    event = DomainEventConverter.to_event(domain_event)
    await event_queue.publish_event(event, topic="inventory-events")

    return InventoryRecordMapper.entity_to_dto(created)


@inventory_router.get(
    "",
    response_model=List[InventoryRecordDTO],
)
async def list_inventory_records_for_shipment(
    warehouse_id: UUID,
    shipment_id: UUID,
    service: InventoryService = Depends(get_inventory_service),
):
    """
    Получить записи инвентаря по shipment_id (для конкретного склада).
    """
    records = await service.list_records_by_shipment(shipment_id)
    records = [r for r in records if r.warehouse_id == warehouse_id]
    return [InventoryRecordMapper.entity_to_dto(r) for r in records]


@inventory_router.get(
    "/{record_id}",
    response_model=InventoryRecordDTO,
)
async def get_inventory_record(
    warehouse_id: UUID,
    record_id: UUID,
    service: InventoryService = Depends(get_inventory_service),
):
    record = await service.get_record(record_id)
    if record is None or record.warehouse_id != warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory record {record_id} not found for warehouse {warehouse_id}",
        )
    return InventoryRecordMapper.entity_to_dto(record)


@inventory_router.patch(
    "/{record_id}",
    response_model=InventoryRecordDTO,
)
async def update_inventory_record(
    warehouse_id: UUID,
    record_id: UUID,
    dto: InventoryRecordUpdateDTO,
    service: InventoryService = Depends(get_inventory_service),
    event_queue: EventQueuePort = Depends(get_event_queue),
):
    """
    Обновить запись инвентаря (например, статус) и опубликовать InventoryUpdated.
    """
    record = await service.get_record(record_id)
    if record is None or record.warehouse_id != warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory record {record_id} not found for warehouse {warehouse_id}",
        )

    updated_entity = InventoryRecordMapper.update_entity_from_dto(record, dto)
    saved = await service.create_record(updated_entity)

    domain_event = InventoryUpdated(
        warehouse_id=saved.warehouse_id,
        item_id=str(saved.record_id),
        new_quantity=0,
        updated_at=datetime.now(timezone.utc),
    )
    event = DomainEventConverter.to_event(domain_event)
    await event_queue.publish_event(event, topic="inventory-events")

    return InventoryRecordMapper.entity_to_dto(saved)


@inventory_router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_inventory_record(
    warehouse_id: UUID,
    record_id: UUID,
    service: InventoryService = Depends(get_inventory_service),
    event_queue: EventQueuePort = Depends(get_event_queue),
):
    """
    Удалить запись инвентаря и опубликовать InventoryReleased.
    """
    record = await service.get_record(record_id)
    if record is None or record.warehouse_id != warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory record {record_id} not found for warehouse {warehouse_id}",
        )

    shipment_id = record.shipment_id
    await service.delete_record(record_id)

    domain_event = InventoryReleased(
        warehouse_id=warehouse_id,
        shipment_id=shipment_id,
        items=[],
        released_at=datetime.now(timezone.utc),
        reason="record_deleted",
    )
    event = DomainEventConverter.to_event(domain_event)
    await event_queue.publish_event(event, topic="inventory-events")

    return None
