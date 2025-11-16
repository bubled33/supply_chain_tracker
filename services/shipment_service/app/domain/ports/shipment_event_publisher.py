from abc import ABC, abstractmethod


class ShipmentEventPublisherPort(ABC):
    @abstractmethod
    def publish_shipment_created(self, payload: dict):
        pass

    @abstractmethod
    def publish_shipment_updated(self, payload: dict):
        pass