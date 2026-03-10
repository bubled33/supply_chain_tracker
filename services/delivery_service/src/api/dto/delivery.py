from uuid import UUID
from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel

from src.domain.entities.delivery import DeliveryStatus


class DeliveryCreateDTO(BaseModel):
    shipment_id: UUID
    courier_id: UUID
    estimated_arrival: Optional[date] = None
    status: Optional[DeliveryStatus] = DeliveryStatus.ASSIGNED


class DeliveryDTO(BaseModel):
    delivery_id: UUID
    shipment_id: UUID
    courier_id: UUID
    status: DeliveryStatus
    created_at: datetime
    updated_at: datetime
    estimated_arrival: Optional[date] = None
    actual_arrival: Optional[date] = None

    model_config = {"from_attributes": True}


class DeliveryUpdateDTO(BaseModel):
    courier_id: Optional[UUID] = None
    status: Optional[DeliveryStatus] = None
    estimated_arrival: Optional[date] = None
    actual_arrival: Optional[date] = None
