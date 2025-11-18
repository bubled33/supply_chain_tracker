from typing import List, Optional
from uuid import UUID

import asyncpg

from services.shipment_service.domain.entities.shipment import Shipment
from services.shipment_service.domain.errors import ShipmentNotFoundError
from services.shipment_service.domain.ports import ShipmentRepositoryPort


class PostgresShipmentRepository(ShipmentRepositoryPort):
    """Асинхронный репозиторий для Shipments через asyncpg"""

    def __init__(self, pool: asyncpg.Pool):
        """
        Args:
            pool: asyncpg connection pool
        """
        self._pool = pool

    async def save(self, shipment: Shipment) -> Shipment:
        """Создать или обновить shipment через UPSERT"""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO shipments (shipment_id, origin, destination, status, created_at, updated_at)
                VALUES ($1, $2, $3, $4, NOW(), NOW())
                ON CONFLICT (shipment_id) 
                DO UPDATE SET
                    origin = EXCLUDED.origin,
                    destination = EXCLUDED.destination,
                    status = EXCLUDED.status,
                    updated_at = NOW()
                RETURNING shipment_id, origin, destination, status, created_at, updated_at
            """, shipment.shipment_id, shipment.origin, shipment.destination, shipment.status)

            return self._row_to_entity(row)

    async def get(self, shipment_id: UUID) -> Optional[Shipment]:
        """Получить shipment по ID"""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT shipment_id, origin, destination, status, created_at, updated_at
                FROM shipments
                WHERE shipment_id = $1
            """, shipment_id)

            return self._row_to_entity(row) if row else None

    async def delete(self, shipment_id: UUID) -> None:
        """Удалить shipment"""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM shipments WHERE shipment_id = $1",
                shipment_id
            )
            # result будет вида "DELETE 1" или "DELETE 0"
            if result == "DELETE 0":
                raise ShipmentNotFoundError(f"Shipment {shipment_id} not found")

    async def get_all(self) -> List[Shipment]:
        """Получить все shipments"""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT shipment_id, origin, destination, status, created_at, updated_at
                FROM shipments
                ORDER BY created_at DESC
            """)
            return [self._row_to_entity(row) for row in rows]

    @staticmethod
    def _row_to_entity(row) -> Shipment:
        """Преобразовать asyncpg.Record в entity"""
        return Shipment(
            shipment_id=row['shipment_id'],
            origin=row['origin'],
            destination=row['destination'],
            status=row['status'],
        )
