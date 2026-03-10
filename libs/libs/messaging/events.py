from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Type, Tuple
from datetime import datetime
import uuid
from .base import Event


@dataclass
class ShipmentCreated:
    shipment_id: uuid.UUID
    origin: str
    destination: str
    items: List[Dict]


@dataclass
class ShipmentUpdated:
    shipment_id: uuid.UUID
    status: str
    updated_at: datetime


@dataclass
class ShipmentCancelled:
    shipment_id: uuid.UUID
    reason: str
    cancelled_at: datetime


@dataclass
class ShipmentDispatched:
    shipment_id: uuid.UUID
    warehouse_id: uuid.UUID
    dispatched_at: datetime


@dataclass
class InventoryReserved:
    warehouse_id: uuid.UUID
    shipment_id: uuid.UUID
    items: List[Dict]
    reserved_at: datetime


@dataclass
class InventoryReleased:
    warehouse_id: uuid.UUID
    shipment_id: uuid.UUID
    items: List[Dict]
    released_at: datetime
    reason: str


@dataclass
class InventoryInsufficient:
    warehouse_id: uuid.UUID
    shipment_id: uuid.UUID
    missing_items: List[Dict]


@dataclass
class InventoryUpdated:
    warehouse_id: uuid.UUID
    item_id: str
    new_quantity: int
    updated_at: datetime


@dataclass
class CourierAssigned:
    delivery_id: uuid.UUID
    courier_id: uuid.UUID
    shipment_id: uuid.UUID
    estimated_delivery: datetime
    assigned_at: datetime


@dataclass
class CourierUnassigned:
    delivery_id: uuid.UUID
    courier_id: uuid.UUID
    reason: str
    unassigned_at: datetime


@dataclass
class DeliveryStarted:
    delivery_id: uuid.UUID
    courier_id: uuid.UUID
    pickup_location: str
    started_at: datetime


@dataclass
class DeliveryInTransit:
    delivery_id: uuid.UUID
    current_location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    updated_at: Optional[datetime] = None


@dataclass
class DeliveryCompleted:
    delivery_id: uuid.UUID
    delivered_at: datetime
    recipient_name: Optional[str] = None
    recipient_signature: Optional[str] = None


@dataclass
class DeliveryFailed:
    delivery_id: uuid.UUID
    reason: str
    failed_at: datetime
    retry_scheduled: Optional[datetime] = None


@dataclass
class BlockchainRecorded:
    record_id: uuid.UUID
    shipment_id: uuid.UUID
    transaction_hash: str
    block_number: Optional[int] = None
    recorded_at: Optional[datetime] = None


@dataclass
class BlockchainVerified:
    record_id: uuid.UUID
    shipment_id: uuid.UUID
    transaction_hash: str
    verified_at: datetime
    confirmations: int


@dataclass
class SagaStarted:
    saga_id: uuid.UUID
    saga_type: str
    initiated_by: str
    started_at: datetime


@dataclass
class SagaCompleted:
    saga_id: uuid.UUID
    saga_type: str
    completed_at: datetime


@dataclass
class SagaFailed:
    saga_id: uuid.UUID
    saga_type: str
    error_message: str
    failed_at: datetime


@dataclass
class SagaCompensating:
    saga_id: uuid.UUID
    saga_type: str
    failed_step: str
    compensating_at: datetime


class DomainEventConverter:

    _EVENT_TYPE_MAP: Dict[Type, Tuple[str, str, str]] = {
        ShipmentCreated: ("shipment.created", "shipment", "shipment_id"),
        ShipmentUpdated: ("shipment.updated", "shipment", "shipment_id"),
        ShipmentCancelled: ("shipment.cancelled", "shipment", "shipment_id"),
        ShipmentDispatched: ("shipment.dispatched", "shipment", "shipment_id"),

        InventoryReserved: ("inventory.reserved", "warehouse", "warehouse_id"),
        InventoryReleased: ("inventory.released", "warehouse", "warehouse_id"),
        InventoryInsufficient: ("inventory.insufficient", "warehouse", "warehouse_id"),
        InventoryUpdated: ("inventory.updated", "warehouse", "warehouse_id"),

        CourierAssigned: ("courier.assigned", "delivery", "delivery_id"),
        CourierUnassigned: ("courier.unassigned", "delivery", "delivery_id"),
        DeliveryStarted: ("delivery.started", "delivery", "delivery_id"),
        DeliveryInTransit: ("delivery.in_transit", "delivery", "delivery_id"),
        DeliveryCompleted: ("delivery.completed", "delivery", "delivery_id"),
        DeliveryFailed: ("delivery.failed", "delivery", "delivery_id"),

        BlockchainRecorded: ("blockchain.recorded", "blockchain_record", "record_id"),
        BlockchainVerified: ("blockchain.verified", "blockchain_record", "record_id"),

        SagaStarted: ("saga.started", "saga", "saga_id"),
        SagaCompleted: ("saga.completed", "saga", "saga_id"),
        SagaFailed: ("saga.failed", "saga", "saga_id"),
        SagaCompensating: ("saga.compensating", "saga", "saga_id"),
    }


    @classmethod
    def to_event(
            cls,
            domain_event: any,
            correlation_id: Optional[uuid.UUID] = None
    ) -> Event:
        event_type_class = type(domain_event)

        if event_type_class not in cls._EVENT_TYPE_MAP:
            raise ValueError(
                f"Unknown domain event: {event_type_class.__name__}. "
                f"Register it in DomainEventConverter._EVENT_TYPE_MAP"
            )

        event_type, aggregate_type, id_field = cls._EVENT_TYPE_MAP[event_type_class]
        aggregate_id = getattr(domain_event, id_field)

        payload = asdict(domain_event)
        payload = cls._serialize_payload(payload)

        return Event(
            event_type=event_type,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            payload=payload,
            correlation_id=correlation_id
        )

    @classmethod
    def get_event_type_name(cls, event_class: Type) -> str:
        if event_class not in cls._EVENT_TYPE_MAP:
            raise ValueError(f"Unknown event class: {event_class.__name__}")
        return cls._EVENT_TYPE_MAP[event_class][0]

    @staticmethod
    def _serialize_payload(payload: Dict) -> Dict:
        serialized = {}
        for key, value in payload.items():
            if isinstance(value, uuid.UUID):
                serialized[key] = str(value)
            elif isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, list):
                serialized[key] = [
                    DomainEventConverter._serialize_payload(item) if isinstance(item, dict) else item
                    for item in value
                ]
            elif isinstance(value, dict):
                serialized[key] = DomainEventConverter._serialize_payload(value)
            else:
                serialized[key] = value
        return serialized
