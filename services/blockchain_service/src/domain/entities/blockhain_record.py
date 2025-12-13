from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict
from uuid import UUID, uuid4


class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"


@dataclass
class BlockchainRecord:
    tx_hash: str
    shipment_id: UUID
    payload: Dict  # Данные, которые мы записали

    record_id: UUID = field(default_factory=uuid4)
    status: TransactionStatus = TransactionStatus.PENDING

    # Метаданные
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    confirmed_at: Optional[datetime] = None
    block_number: Optional[int] = None
    error_message: Optional[str] = None
    gas_used: Optional[int] = None

    def confirm(self, block_number: int, gas_used: int, timestamp: datetime):
        """Перевод в статус подтверждено"""
        self.status = TransactionStatus.CONFIRMED
        self.block_number = block_number
        self.gas_used = gas_used
        self.confirmed_at = timestamp

    def fail(self, error: str):
        """Перевод в статус ошибки"""
        self.status = TransactionStatus.FAILED
        self.error_message = error

    def to_dict(self) -> dict:
        return {
            "record_id": str(self.record_id),
            "shipment_id": str(self.shipment_id),
            "tx_hash": self.tx_hash,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
        }
