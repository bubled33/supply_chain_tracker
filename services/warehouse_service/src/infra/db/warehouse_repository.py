from typing import List, Optional
from uuid import UUID

import asyncpg

from libs.value_objects.location import Location

from src.domain.entities import Warehouse
from src.domain.ports.warehouse_repository import WarehouseRepositoryPort


class AsyncPostgresWarehouseRepository(WarehouseRepositoryPort):
    """Асинхронный репозиторий для Warehouse"""

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def save(self, warehouse: Warehouse) -> Warehouse:
        """
        UPSERT склада по warehouse_id.
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO warehouses (
                    warehouse_id,
                    name,
                    location
                )
                VALUES ($1, $2, $3)
                ON CONFLICT (warehouse_id)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    location = EXCLUDED.location
                RETURNING
                    warehouse_id,
                    name,
                    location
                """,
                warehouse.warehouse_id,
                warehouse.name,
                warehouse.location.value,  # Location VO
            )

        return self._row_to_entity(row)

    async def get(self, warehouse_id: UUID) -> Optional[Warehouse]:
        """Получить склад по ID."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    warehouse_id,
                    name,
                    location
                FROM warehouses
                WHERE warehouse_id = $1
                """,
                warehouse_id,
            )

        return self._row_to_entity(row) if row else None

    async def get_all(self) -> List[Warehouse]:
        """Получить все склады."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    warehouse_id,
                    name,
                    location
                FROM warehouses
                ORDER BY name
                """
            )

        return [self._row_to_entity(row) for row in rows]

    async def delete(self, warehouse_id: UUID) -> None:
        """Удалить склад по ID."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM warehouses WHERE warehouse_id = $1",
                warehouse_id,
            )

    @staticmethod
    def _row_to_entity(row: asyncpg.Record) -> Warehouse:
        """Преобразовать row в Warehouse."""
        return Warehouse(
            warehouse_id=row["warehouse_id"],
            name=row["name"],
            location=Location(row["location"]),
        )
