from uuid import UUID, uuid4
from datetime import datetime


class SagaEvent:
    def __init__(
        self,
        saga_id: UUID,
        event_type: str,
        payload: dict,
        event_id: UUID = None,
        timestamp: datetime = None
    ):
        self.event_id: UUID = event_id or uuid4()
        self.saga_id: UUID = saga_id
        self.event_type: str = event_type
        self.payload: dict = payload
        self.timestamp: datetime = timestamp or datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            "event_id": str(self.event_id),
            "saga_id": str(self.saga_id),
            "event_type": self.event_type,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
        }

    def __repr__(self):
        return f"<SagaEvent {self.event_id} Type:{self.event_type} Timestamp:{self.timestamp}>"

