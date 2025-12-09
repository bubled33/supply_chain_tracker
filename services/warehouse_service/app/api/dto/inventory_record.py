from dataclasses import dataclass
from uuid import UUID
from datetime import datetime
from typing import Optional

from app.domain.entities.inventory_record import InventoryStatus


@dataclass
class InventoryRecordCreateDTO:
    """DTO для создания новой записи инвентаря."""
    shipment_id: UUID
    warehouse_id: UUID
    status: Optional[InventoryStatus] = InventoryStatus.RECEIVED


@dataclass
class InventoryRecordDTO:
    """DTO для ответа API / представления записи инвентаря."""
    record_id: UUID
    shipment_id: UUID
    warehouse_id: UUID
    status: InventoryStatus
    received_at: datetime
    updated_at: datetime


@dataclass
class InventoryRecordUpdateDTO:
    """
    DTO для обновления записи инвентаря.
    Сейчас меняется только статус, но можно расширить при необходимости.
    """
    status: Optional[InventoryStatus] = None
