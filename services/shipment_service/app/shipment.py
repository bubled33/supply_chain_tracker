from uuid import UUID
from typing import List

from services.shipment_service.domain.entities.shipment import Shipment


class ShipmentService:
    def __init__(
        self,
    ):
        pass

    # ---- CRUD ----
    def create(self, shipment: Shipment) -> Shipment:
        pass

    def get(self, shipment_id: UUID) -> Shipment:
        pass

    def update(self, shipment: Shipment) -> Shipment:
        pass

    def delete(self, shipment_id: UUID) -> None:
        pass

    def get_all(self) -> List[Shipment]:
        pass

    # ---- Бизнес методы ----
    def add_item(self, shipment: Shipment, item) -> Shipment:
        pass

    def mark_as_created(self, shipment: Shipment) -> Shipment:
        pass

    def mark_as_received(self, shipment: Shipment) -> Shipment:
        pass

    def mark_as_ready_for_delivery(self, shipment: Shipment) -> Shipment:
        pass

    def mark_as_in_transit(self, shipment: Shipment) -> Shipment:
        pass

    def mark_as_delivered(self, shipment: Shipment, arrival_date) -> Shipment:
        pass

    def mark_as_completed(self, shipment: Shipment) -> Shipment:
        pass
