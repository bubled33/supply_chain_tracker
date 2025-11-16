from enum import Enum
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID, uuid4
from .item import Item  # импортируем Item из отдельного файла


class ShipmentStatus(str, Enum):
    CREATED = "created"
    RECEIVED = "received"
    READY_FOR_DELIVERY = "ready_for_delivery"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    COMPLETED = "completed"  # финальный on-chain статус


class Shipment:
    def __init__(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        arrival_date: Optional[date] = None,
        shipment_id: Optional[UUID] = None,
        status: ShipmentStatus = ShipmentStatus.CREATED,
        items: Optional[List[Item]] = None
    ):
        self.shipment_id: UUID = shipment_id or uuid4()
        self.origin: str = origin
        self.destination: str = destination
        self.departure_date: date = departure_date
        self.arrival_date: Optional[date] = arrival_date
        self.status: ShipmentStatus = status
        self.items: List[Item] = items or []
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()

    def add_item(self, item: Item):
        self.items.append(item)
        self.updated_at = datetime.utcnow()

    def update_status(self, new_status: ShipmentStatus):
        self.status = new_status
        self.updated_at = datetime.utcnow()

    def mark_delivered(self, arrival_date: date):
        self.arrival_date = arrival_date
        self.update_status(ShipmentStatus.DELIVERED)

    def to_dict(self) -> dict:
        return {
            "shipment_id": str(self.shipment_id),
            "origin": self.origin,
            "destination": self.destination,
            "departure_date": str(self.departure_date),
            "arrival_date": str(self.arrival_date) if self.arrival_date else None,
            "status": self.status.value,
            "items": [vars(item) for item in self.items],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<Shipment {self.shipment_id} {self.status}>"
