from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from datetime import datetime, timezone
import uuid


@dataclass
class Event:
    """Базовый класс для всех событий"""
    event_type: str
    aggregate_id: uuid.UUID
    aggregate_type: str
    payload: Dict[str, Any]

    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: Optional[uuid.UUID] = None  # Saga ID


@dataclass
class Command:
    """Базовый класс для команд"""
    command_type: str
    aggregate_id: uuid.UUID
    payload: Dict[str, Any]

    command_id: uuid.UUID = field(default_factory=uuid.uuid4)
    correlation_id: Optional[uuid.UUID] = None  # Saga ID
