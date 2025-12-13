# services/saga_coordinator/app/domain/entities/saga_instance.py
from dataclasses import dataclass, field
from uuid import UUID
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class SagaStatus(str, Enum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"


@dataclass
class SagaInstance:
    saga_id: UUID
    saga_type: str
    shipment_id: UUID
    warehouse_id: Optional[UUID] = None
    delivery_id: Optional[UUID] = None
    status: SagaStatus = SagaStatus.STARTED
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    failed_step: Optional[str] = None
    error_message: Optional[str] = None

    def mark_completed(self):
        self.status = SagaStatus.COMPLETED
        self.updated_at = datetime.now(timezone.utc)

    def mark_failed(self, step: str, error: str):
        self.status = SagaStatus.FAILED
        self.failed_step = step
        self.error_message = error
        self.updated_at = datetime.now(timezone.utc)

    def mark_compensating(self, step: str):
        self.status = SagaStatus.COMPENSATING
        self.failed_step = step
        self.updated_at = datetime.now(timezone.utc)
