from abc import ABC, abstractmethod
from uuid import UUID

from services.shipment_service.app.domain.entities.shipment import Shipment


class ShipmentRepositoryPort(ABC):
    @abstractmethod
    def add_shipment(self, shipment: Shipment) -> Shipment:
        pass

    @abstractmethod
    def get_shipment(self, shipment_id: UUID) -> Shipment:
        pass

    @abstractmethod
    def update_shipment(self, shipment: Shipment) -> Shipment:
        pass

    @abstractmethod
    def list_shipments(self) -> list[Shipment]:
        pass
