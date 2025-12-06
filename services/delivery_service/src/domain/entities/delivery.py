from uuid import UUID, uuid4
from datetime import datetime, date
from enum import Enum
from .courier import Courier


class DeliveryStatus(str, Enum):
    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CONFIRMED = "confirmed"


class Delivery:
    def __init__(
        self,
        shipment_id: UUID,
        courier: Courier,
        status: DeliveryStatus = DeliveryStatus.ASSIGNED,
        delivery_id: UUID = None,
        estimated_arrival: date = None,
        actual_arrival: date = None
    ):
        self.delivery_id: UUID = delivery_id or uuid4()
        self.shipment_id: UUID = shipment_id
        self.courier: Courier = courier
        self.status: DeliveryStatus = status
        self.estimated_arrival: date = estimated_arrival
        self.actual_arrival: date = actual_arrival
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()

    def update_status(self, new_status: DeliveryStatus):
        self.status = new_status
        self.updated_at = datetime.utcnow()

    def mark_delivered(self, actual_arrival: date):
        self.actual_arrival = actual_arrival
        self.update_status(DeliveryStatus.DELIVERED)

    def to_dict(self) -> dict:
        return {
            "delivery_id": str(self.delivery_id),
            "shipment_id": str(self.shipment_id),
            "courier_id": str(self.courier.courier_id),
            "status": self.status.value,
            "estimated_arrival": str(self.estimated_arrival) if self.estimated_arrival else None,
            "actual_arrival": str(self.actual_arrival) if self.actual_arrival else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<Delivery {self.delivery_id} Shipment:{self.shipment_id} Status:{self.status}>"
