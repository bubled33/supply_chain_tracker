from typing import List, Optional
from uuid import UUID
import asyncpg

from src.domain.entities import Courier
from src.domain.ports.courier_repository import CourierRepositoryPort


class AsyncPostgresCourierRepository(CourierRepositoryPort):
    """Асинхронный репозиторий для Courier"""

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def save(self, courier: Courier) -> Courier:
        """UPSERT для courier"""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO couriers (courier_id, name, contact_info)
                VALUES ($1, $2, $3)
                ON CONFLICT (courier_id)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    contact_info = EXCLUDED.contact_info
                RETURNING courier_id, name, contact_info
            """, courier.courier_id, courier.name, courier.contact_info)

            return self._row_to_entity(row)

    async def get(self, courier_id: UUID) -> Optional[Courier]:
        """Получить курьера по ID"""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT courier_id, name, contact_info
                FROM couriers
                WHERE courier_id = $1
            """, courier_id)

            return self._row_to_entity(row) if row else None

    async def get_all(self) -> List[Courier]:
        """Получить всех курьеров"""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT courier_id, name, contact_info
                FROM couriers
                ORDER BY name
            """)
            return [self._row_to_entity(row) for row in rows]

    async def delete(self, courier_id: UUID) -> None:
        """Удалить курьера"""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM couriers WHERE courier_id = $1",
                courier_id
            )
            # if result == "DELETE 0":
            #    raise CourierNotFoundError(f"Courier {courier_id} not found")

    @staticmethod
    def _row_to_entity(row) -> Courier:
        """Преобразовать row в entity"""
        return Courier(
            courier_id=row['courier_id'],
            name=row['name'],
            contact_info=row['contact_info']
        )
