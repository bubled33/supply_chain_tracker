from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


@dataclass
class ComponentHealth:
    """Статус отдельного компонента системы."""
    status: HealthStatus
    details: Optional[Dict[str, str]] = None
    latency_ms: Optional[float] = None

    def to_dict(self) -> dict:
        """Преобразование в словарь для JSON-ответа."""
        result = {"status": self.status.value}
        if self.details:
            result["details"] = self.details
        if self.latency_ms is not None:
            result["latency_ms"] = self.latency_ms
        return result


@dataclass
class HealthResponse:
    """Общий ответ на health/ready запрос."""
    service: str
    status: HealthStatus
    components: Dict[str, ComponentHealth] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Преобразование в словарь для JSON-ответа."""
        return {
            "service": self.service,
            "status": self.status.value,
            "components": {
                name: component.to_dict()
                for name, component in self.components.items()
            } if self.components else {}
        }
