import json
from typing import List, Optional
import asyncpg

from src.domain.entities.blockhain_record import BlockchainRecord, TransactionStatus
from src.domain.ports.blockhain_repository import BlockchainRepositoryPort


class AsyncPostgresBlockchainRepository(BlockchainRepositoryPort):
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def save(self, record: BlockchainRecord) -> BlockchainRecord:
        async with self._pool.acquire() as conn:
            # Сериализуем payload в строку для JSONB
            payload_json = json.dumps(record.payload)

            row = await conn.fetchrow("""
                INSERT INTO blockchain_records (
                    record_id, shipment_id, tx_hash, status, payload, 
                    created_at, confirmed_at, block_number, error_message, gas_used
                )
                VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9, $10)
                ON CONFLICT (record_id)
                DO UPDATE SET
                    status = EXCLUDED.status,
                    confirmed_at = EXCLUDED.confirmed_at,
                    block_number = EXCLUDED.block_number,
                    error_message = EXCLUDED.error_message,
                    gas_used = EXCLUDED.gas_used
                RETURNING *
            """,
                                      record.record_id,
                                      record.shipment_id,
                                      record.tx_hash,
                                      record.status.value,
                                      payload_json,
                                      record.created_at,
                                      record.confirmed_at,
                                      record.block_number,
                                      record.error_message,
                                      record.gas_used
                                      )

            return self._row_to_entity(row)

    async def get_by_tx_hash(self, tx_hash: str) -> Optional[BlockchainRecord]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM blockchain_records 
                WHERE tx_hash = $1
            """, tx_hash)

            return self._row_to_entity(row) if row else None

    async def get_pending_records(self, limit: int = 100) -> List[BlockchainRecord]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM blockchain_records 
                WHERE status = 'PENDING'
                ORDER BY created_at ASC
                LIMIT $1
            """, limit)

            return [self._row_to_entity(row) for row in rows]

    @staticmethod
    def _row_to_entity(row) -> BlockchainRecord:
        payload = row['payload']
        if isinstance(payload, str):
            payload = json.loads(payload)

        return BlockchainRecord(
            record_id=row['record_id'],
            shipment_id=row['shipment_id'],
            tx_hash=row['tx_hash'],
            status=TransactionStatus(row['status']),
            payload=payload,
            created_at=row['created_at'],
            confirmed_at=row['confirmed_at'],
            block_number=row['block_number'],
            error_message=row['error_message'],
            gas_used=row['gas_used']
        )
