from typing import Protocol, List, Optional
from uuid import UUID

from src.domain.entities.blockchain_record import BlockchainRecord


class BlockchainRepositoryPort(Protocol):
    """Порт для работы с записями блокчейна"""

    async def save(self, record: BlockchainRecord) -> BlockchainRecord:
        """
        Сохранить запись (UPSERT).
        Используется при создании (PENDING) и при обновлении статуса.
        """
        ...

    async def get_by_tx_hash(self, tx_hash: str) -> Optional[BlockchainRecord]:
        """Получить запись по хешу транзакции"""
        ...

    async def get_pending_records(self, limit: int = 100) -> List[BlockchainRecord]:
        """
        Получить список транзакций, которые ожидают подтверждения.
        Используется фоновым монитором.
        """
        ...
