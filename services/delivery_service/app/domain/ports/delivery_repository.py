from abc import ABC, abstractmethod
from uuid import UUID

from services.delivery_service.app.domain.entities import Delivery


class DeliveryRepositoryPort(ABC):
    @abstractmethod
    def add_delivery(self, delivery: Delivery) -> Delivery:
        pass

    @abstractmethod
    def get_delivery(self, delivery_id: UUID) -> Delivery:
        pass

    @abstractmethod
    def update_delivery(self, delivery: Delivery) -> Delivery:
        pass

    @abstractmethod
    def list_deliveries_by_shipment(self, shipment_id: UUID) -> list[Delivery]:
        pass
