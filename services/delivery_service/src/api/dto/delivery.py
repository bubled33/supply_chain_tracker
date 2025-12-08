from dataclasses import dataclass
from uuid import UUID
from datetime import datetime, date
from typing import Optional

from src.domain.entities.delivery import DeliveryStatus

@dataclass
class DeliveryCreateDTO:
    """DTO для создания новой доставки"""
    shipment_id: UUID
    courier_id: UUID
    estimated_arrival: Optional[date] = None
    status: Optional[DeliveryStatus] = DeliveryStatus.ASSIGNED

@dataclass
class DeliveryDTO:
    """DTO для ответа API / представления Delivery"""
    delivery_id: UUID
    shipment_id: UUID
    courier_id: UUID
    status: DeliveryStatus
    created_at: datetime
    updated_at: datetime
    estimated_arrival: Optional[date] = None
    actual_arrival: Optional[date] = None

@dataclass
class DeliveryUpdateDTO:
    """
    DTO для обновления доставки.
    Позволяет менять статус, сроки или переназначать курьера.
    """
    courier_id: Optional[UUID] = None
    status: Optional[DeliveryStatus] = None
    estimated_arrival: Optional[date] = None
    actual_arrival: Optional[date] = None
