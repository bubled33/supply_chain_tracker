from abc import abstractmethod, ABC


class InventoryEventPublisherPort(ABC):
    @abstractmethod
    def publish_inventory_received(self, payload: dict):
        pass

    @abstractmethod
    def publish_inventory_ready(self, payload: dict):
        pass