from typing import List, Optional
from uuid import UUID
import asyncpg

from services.shipment_service.domain.entities.item import Item
from services.shipment_service.domain.ports import ItemRepositoryPort
from services.shipment_service.domain.value_objects.quantity import Quantity
from services.shipment_service.domain.value_objects.weight import Weight
from services.shipment_service.domain.errors import ItemNotFoundError


class AsyncPostgresItemRepository(ItemRepositoryPort):
    """Асинхронный репозиторий для Items"""

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def save(self, item: Item) -> Item:
        """UPSERT для item"""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO items (item_id, shipment_id, name, quantity, weight)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (item_id)
                DO UPDATE SET
                    shipment_id = EXCLUDED.shipment_id,
                    name = EXCLUDED.name,
                    quantity = EXCLUDED.quantity,
                    weight = EXCLUDED.weight
                RETURNING item_id, shipment_id, name, quantity, weight
            """, item.item_id, item.shipment_id, item.name,
                                      item.quantity.value, item.weight.value)

            return self._row_to_entity(row)

    async def get(self, item_id: UUID) -> Optional[Item]:
        """Получить item по ID"""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT item_id, shipment_id, name, quantity, weight
                FROM items
                WHERE item_id = $1
            """, item_id)

            return self._row_to_entity(row) if row else None

    async def get_by_shipment(self, shipment_id: UUID) -> List[Item]:
        """Получить все items для shipment"""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT item_id, shipment_id, name, quantity, weight
                FROM items
                WHERE shipment_id = $1
                ORDER BY name
            """, shipment_id)

            return [self._row_to_entity(row) for row in rows]

    async def delete(self, item_id: UUID) -> None:
        """Удалить item"""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM items WHERE item_id = $1",
                item_id
            )
            if result == "DELETE 0":
                raise ItemNotFoundError(f"Item {item_id} not found")

    async def get_all(self) -> List[Item]:
        """Получить все items"""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT item_id, shipment_id, name, quantity, weight
                FROM items
                ORDER BY name
            """)
            return [self._row_to_entity(row) for row in rows]

    @staticmethod
    def _row_to_entity(row) -> Item:
        """Преобразовать row в entity"""
        return Item(
            item_id=row['item_id'],
            shipment_id=row['shipment_id'],
            name=row['name'],
            quantity=Quantity(row['quantity']),
            weight=Weight(row['weight']),
        )
