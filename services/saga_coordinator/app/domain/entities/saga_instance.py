from abc import ABC, abstractmethod
from uuid import UUID, uuid4
from enum import Enum
from datetime import datetime

from services.saga_coordinator.app.domain.entities.saga_event import SagaEvent


class SagaStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SagaInstance:
    def __init__(
        self,
        shipment_id: UUID,
        current_step: str = "created",
        status: SagaStatus = SagaStatus.PENDING,
        saga_id: UUID = None,
        retries: int = 0
    ):
        self.saga_id: UUID = saga_id or uuid4()
        self.shipment_id: UUID = shipment_id
        self.current_step: str = current_step
        self.status: SagaStatus = status
        self.retries: int = retries
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()

    def advance_step(self, next_step: str):
        self.current_step = next_step
        self.status = SagaStatus.IN_PROGRESS
        self.updated_at = datetime.utcnow()

    def mark_completed(self):
        self.status = SagaStatus.COMPLETED
        self.updated_at = datetime.utcnow()

    def mark_failed(self):
        self.status = SagaStatus.FAILED
        self.updated_at = datetime.utcnow()
        self.retries += 1

    def to_dict(self) -> dict:
        return {
            "saga_id": str(self.saga_id),
            "shipment_id": str(self.shipment_id),
            "current_step": self.current_step,
            "status": self.status.value,
            "retries": self.retries,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<SagaInstance {self.saga_id} Shipment:{self.shipment_id} Step:{self.current_step} Status:{self.status}>"
