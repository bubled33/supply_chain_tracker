from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum


class InventoryStatus(str, Enum):
    RECEIVED = "received"
    STORED = "stored"
    READY_FOR_DELIVERY = "ready_for_delivery"
    SHIPPED = "shipped"


class InventoryRecord:
    def __init__(
        self,
        shipment_id: UUID,
        warehouse_id: UUID,
        status: InventoryStatus = InventoryStatus.RECEIVED,
        record_id: UUID = None
    ):
        self.record_id: UUID = record_id or uuid4()
        self.shipment_id: UUID = shipment_id
        self.warehouse_id: UUID = warehouse_id
        self.status: InventoryStatus = status
        self.received_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()

    def update_status(self, new_status: InventoryStatus):
        self.status = new_status
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            "record_id": str(self.record_id),
            "shipment_id": str(self.shipment_id),
            "warehouse_id": str(self.warehouse_id),
            "status": self.status.value,
            "received_at": self.received_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<InventoryRecord {self.record_id} Shipment:{self.shipment_id} Status:{self.status}>"
