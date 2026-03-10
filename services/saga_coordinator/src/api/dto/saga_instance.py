from dataclasses import dataclass
from uuid import UUID
from datetime import datetime
from typing import Optional

from src.domain.entities.saga_instance import SagaStatus


@dataclass
class SagaCreateDTO:
    saga_id: UUID
    saga_type: str
    shipment_id: UUID
    warehouse_id: Optional[UUID] = None
    delivery_id: Optional[UUID] = None


@dataclass
class SagaDTO:
    saga_id: UUID
    saga_type: str
    shipment_id: UUID
    status: SagaStatus
    started_at: datetime
    updated_at: datetime

    warehouse_id: Optional[UUID] = None
    delivery_id: Optional[UUID] = None

    failed_step: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class SagaUpdateDTO:
    warehouse_id: Optional[UUID] = None
    delivery_id: Optional[UUID] = None
    status: Optional[SagaStatus] = None
    failed_step: Optional[str] = None
    error_message: Optional[str] = None
