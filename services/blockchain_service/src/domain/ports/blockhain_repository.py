from typing import Protocol, List, Optional
from uuid import UUID

from src.domain.entities.blockhain_record import BlockchainRecord


class BlockchainRepositoryPort(Protocol):

    async def save(self, record: BlockchainRecord) -> BlockchainRecord:
        ...

    async def get_by_tx_hash(self, tx_hash: str) -> Optional[BlockchainRecord]:
        ...

    async def get_pending_records(self, limit: int = 100) -> List[BlockchainRecord]:
        ...
