from typing import Protocol

class ShipmentEventPublisherPort(Protocol):
    def publish_shipment_created(self, payload: dict) -> None:
        ...

    def publish_shipment_updated(self, payload: dict) -> None:
        ...
