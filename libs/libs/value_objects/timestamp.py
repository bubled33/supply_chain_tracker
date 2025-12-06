from dataclasses import dataclass
from datetime import datetime, timezone

from libs.errors.value_objects import TimestampError


@dataclass(frozen=True)
class Timestamp:
    value: datetime

    def __post_init__(self):
        if self.value.tzinfo != timezone.utc:
            raise TimestampError("Timestamp must be UTC.")

    def isoformat(self) -> str:
        """Возвращает строку в ISO 8601 формате с указанием UTC"""
        return self.value.isoformat()
