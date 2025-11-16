from abc import ABC, abstractmethod


class DeliveryEventPublisherPort(ABC):
    @abstractmethod
    def publish_delivery_assigned(self, payload: dict):
        pass

    @abstractmethod
    def publish_delivery_in_transit(self, payload: dict):
        pass

    @abstractmethod
    def publish_delivery_completed(self, payload: dict):
        pass
