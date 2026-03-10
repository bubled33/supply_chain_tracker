from dataclasses import dataclass, field
from uuid import UUID
from datetime import datetime
from typing import Optional

from src.domain.entities.inventory_record import InventoryStatus


@dataclass
class InventoryRecordCreateDTO:
    shipment_id: UUID
    warehouse_id: Optional[UUID] = field(default=None)
    status: Optional[InventoryStatus] = InventoryStatus.RECEIVED


@dataclass
class InventoryRecordDTO:
    record_id: UUID
    shipment_id: UUID
    warehouse_id: UUID
    status: InventoryStatus
    received_at: datetime
    updated_at: datetime


@dataclass
class InventoryRecordUpdateDTO:
    status: Optional[InventoryStatus] = None
