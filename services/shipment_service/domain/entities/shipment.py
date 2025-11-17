from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from libs.value_objects.timestamp import Timestamp
from .item import Item
from ..value_objects.shipment_status import ShipmentStatus
from ..value_objects.location import Location

@dataclass
class Shipment:
    origin: Location
    destination: Location
    departure_date: date

    arrival_date: Optional[date] = None
    shipment_id: UUID = field(default_factory=uuid4)
    status: ShipmentStatus = ShipmentStatus.CREATED
    items: List[Item] = field(default_factory=list)

    created_at: Timestamp = field(
        default_factory=lambda: Timestamp(datetime.now(timezone.utc))
    )
    updated_at: Timestamp = field(
        default_factory=lambda: Timestamp(datetime.now(timezone.utc))
    )

    def _touch(self):
        self.updated_at = Timestamp(datetime.now(timezone.utc))

    def add_item(self, item: Item):
        self.items.append(item)
        self._touch()

    def update_status(self, new_status: ShipmentStatus):
        self.status = new_status
        self._touch()

    def mark_delivered(self, arrival_date: date):
        self.arrival_date = arrival_date
        self.update_status(ShipmentStatus.DELIVERED)

    def to_dict(self) -> dict:
        return {
            "shipment_id": str(self.shipment_id),
            "origin": self.origin.__dict__,
            "destination": self.destination.__dict__,
            "departure_date": str(self.departure_date),
            "arrival_date": str(self.arrival_date) if self.arrival_date else None,
            "status": self.status.value,
            "items": [item.to_dict() for item in self.items],
            "created_at": self.created_at.value.isoformat(),
            "updated_at": self.updated_at.value.isoformat(),
        }

    def __repr__(self):
        return f"<Shipment {self.shipment_id} {self.status}>"
