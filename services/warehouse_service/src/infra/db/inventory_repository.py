from typing import List, Optional
from uuid import UUID

import asyncpg

from src.domain.entities import InventoryRecord
from src.domain.entities.inventory_record import InventoryStatus
from src.domain.ports import InventoryRepositoryPort


class AsyncPostgresInventoryRepository(InventoryRepositoryPort):
    """Асинхронный репозиторий для InventoryRecord"""

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def save(self, record: InventoryRecord) -> InventoryRecord:
        """
        UPSERT записи инвентаря по record_id.
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO inventory_records (
                    record_id,
                    shipment_id,
                    warehouse_id,
                    status,
                    received_at,
                    updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (record_id)
                DO UPDATE SET
                    shipment_id = EXCLUDED.shipment_id,
                    warehouse_id = EXCLUDED.warehouse_id,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at
                RETURNING
                    record_id,
                    shipment_id,
                    warehouse_id,
                    status,
                    received_at,
                    updated_at
                """,
                record.record_id,
                record.shipment_id,
                record.warehouse_id,
                record.status.value,
                record.received_at,
                record.updated_at,
            )

        return self._row_to_entity(row)

    async def get(self, record_id: UUID) -> Optional[InventoryRecord]:
        """Получить запись инвентаря по ID."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    record_id,
                    shipment_id,
                    warehouse_id,
                    status,
                    received_at,
                    updated_at
                FROM inventory_records
                WHERE record_id = $1
                """,
                record_id,
            )

        return self._row_to_entity(row) if row else None

    async def list_by_shipment(self, shipment_id: UUID) -> List[InventoryRecord]:
        """Получить все записи инвентаря по shipment_id."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    record_id,
                    shipment_id,
                    warehouse_id,
                    status,
                    received_at,
                    updated_at
                FROM inventory_records
                WHERE shipment_id = $1
                ORDER BY received_at
                """,
                shipment_id,
            )

        return [self._row_to_entity(row) for row in rows]

    async def delete(self, record_id: UUID) -> None:
        """Удалить запись инвентаря по ID."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM inventory_records WHERE record_id = $1",
                record_id,
            )

    @staticmethod
    def _row_to_entity(row: asyncpg.Record) -> InventoryRecord:
        """Преобразовать row в InventoryRecord."""
        return InventoryRecord(
            record_id=row["record_id"],
            shipment_id=row["shipment_id"],
            warehouse_id=row["warehouse_id"],
            status=InventoryStatus(row["status"]),
        )
