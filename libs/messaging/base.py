import json
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

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """
        Десериализовать dict в Event.

        Args:
            data: Dictionary с данными события из Kafka

        Returns:
            Event instance
        """
        return cls(
            event_type=data['event_type'],
            aggregate_id=uuid.UUID(data['aggregate_id']),
            aggregate_type=data['aggregate_type'],
            payload=data['payload'],
            event_id=uuid.UUID(data['event_id']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            correlation_id=uuid.UUID(data['correlation_id']) if data.get('correlation_id') else None
        )

    @classmethod
    def from_json(cls, json_string: str) -> 'Event':
        """
        Десериализовать JSON строку в Event.

        Args:
            json_string: JSON строка с данными события

        Returns:
            Event instance
        """
        data = json.loads(json_string)
        return cls.from_dict(data)

    def to_dict(self) -> Dict[str, Any]:
        """Сериализовать Event в dict для Kafka"""
        return {
            'event_id': str(self.event_id),
            'event_type': self.event_type,
            'aggregate_id': str(self.aggregate_id),
            'aggregate_type': self.aggregate_type,
            'payload': self.payload,
            'timestamp': self.timestamp.isoformat(),
            'correlation_id': str(self.correlation_id) if self.correlation_id else None
        }

    def to_json(self) -> str:
        """Сериализовать Event в JSON для Kafka"""
        return json.dumps(self.to_dict())

@dataclass
class Command:
    """Базовый класс для команд"""
    command_type: str
    aggregate_id: uuid.UUID
    payload: Dict[str, Any]

    command_id: uuid.UUID = field(default_factory=uuid.uuid4)
    correlation_id: Optional[uuid.UUID] = None  # Saga ID

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Command':
        """Десериализовать dict в Command"""
        return cls(
            command_type=data['command_type'],
            aggregate_id=uuid.UUID(data['aggregate_id']),
            payload=data['payload'],
            command_id=uuid.UUID(data['command_id']),
            correlation_id=uuid.UUID(data['correlation_id']) if data.get('correlation_id') else None
        )

    @classmethod
    def from_json(cls, json_string: str) -> 'Command':
        """Десериализовать JSON строку в Command"""
        data = json.loads(json_string)
        return cls.from_dict(data)