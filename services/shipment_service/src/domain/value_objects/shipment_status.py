from enum import Enum


class ShipmentStatus(str, Enum):
    CREATED = "created"
    RECEIVED = "received"
    READY_FOR_DELIVERY = "ready_for_delivery"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    COMPLETED = "completed"  # финальный on-chain статус
