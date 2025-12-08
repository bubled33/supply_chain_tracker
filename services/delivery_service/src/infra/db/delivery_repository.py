from typing import List, Optional
from uuid import UUID
import asyncpg

from src.domain.entities import Delivery, Courier
from src.domain.entities.delivery import DeliveryStatus
from src.domain.ports import DeliveryRepositoryPort

class AsyncPostgresDeliveryRepository(DeliveryRepositoryPort):
    """Асинхронный репозиторий для Delivery"""

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    # Общий SQL запрос для выборки с JOIN курьера
    _SELECT_QUERY = """
        SELECT 
            d.delivery_id, d.shipment_id, d.status, 
            d.estimated_arrival, d.actual_arrival, 
            d.created_at, d.updated_at,
            c.courier_id, c.name as courier_name, c.contact_info as courier_contact
        FROM deliveries d
        JOIN couriers c ON d.courier_id = c.courier_id
    """

    async def save(self, delivery: Delivery) -> Delivery:
        """UPSERT для delivery. Сохраняем ID курьера как foreign key"""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO deliveries (
                    delivery_id, shipment_id, courier_id, status, 
                    estimated_arrival, actual_arrival, created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (delivery_id)
                DO UPDATE SET
                    shipment_id = EXCLUDED.shipment_id,
                    courier_id = EXCLUDED.courier_id,
                    status = EXCLUDED.status,
                    estimated_arrival = EXCLUDED.estimated_arrival,
                    actual_arrival = EXCLUDED.actual_arrival,
                    updated_at = EXCLUDED.updated_at
                RETURNING 
                    delivery_id, shipment_id, status, 
                    estimated_arrival, actual_arrival, 
                    created_at, updated_at
            """,
                                      delivery.delivery_id,
                                      delivery.shipment_id,
                                      delivery.courier.courier_id,
                                      delivery.status.value,
                                      delivery.estimated_arrival,
                                      delivery.actual_arrival,
                                      delivery.created_at,
                                      delivery.updated_at
                                      )

            return delivery

    async def get(self, delivery_id: UUID) -> Optional[Delivery]:
        """Получить доставку по ID вместе с курьером"""
        async with self._pool.acquire() as conn:
            query = self._SELECT_QUERY + " WHERE d.delivery_id = $1"
            row = await conn.fetchrow(query, delivery_id)

            return self._row_to_entity(row) if row else None

    async def get_by_shipment(self, shipment_id: UUID) -> List[Delivery]:
        """Получить доставки по ID отправления"""
        async with self._pool.acquire() as conn:
            query = self._SELECT_QUERY + " WHERE d.shipment_id = $1 ORDER BY d.created_at DESC"
            rows = await conn.fetch(query, shipment_id)
            return [self._row_to_entity(row) for row in rows]

    async def get_by_courier(self, courier_id: UUID) -> List[Delivery]:
        """Получить доставки конкретного курьера"""
        async with self._pool.acquire() as conn:
            query = self._SELECT_QUERY + " WHERE d.courier_id = $1 ORDER BY d.created_at DESC"
            rows = await conn.fetch(query, courier_id)
            return [self._row_to_entity(row) for row in rows]

    async def get_by_status(self, status: DeliveryStatus) -> List[Delivery]:
        """Получить доставки по статусу"""
        async with self._pool.acquire() as conn:
            query = self._SELECT_QUERY + " WHERE d.status = $1 ORDER BY d.created_at"
            rows = await conn.fetch(query, status.value)
            return [self._row_to_entity(row) for row in rows]

    async def get_all(self) -> List[Delivery]:
        """Получить все доставки"""
        async with self._pool.acquire() as conn:
            query = self._SELECT_QUERY + " ORDER BY d.created_at DESC"
            rows = await conn.fetch(query)
            return [self._row_to_entity(row) for row in rows]

    async def delete(self, delivery_id: UUID) -> None:
        """Удалить доставку"""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM deliveries WHERE delivery_id = $1",
                delivery_id
            )

    @staticmethod
    def _row_to_entity(row) -> Delivery:
        """
        Преобразовать row (результат JOIN) в entity Delivery с вложенным Courier.
        """
        courier = Courier(
            courier_id=row['courier_id'],
            name=row['courier_name'],
            contact_info=row['courier_contact_info']
        )

        delivery = Delivery(
            delivery_id=row['delivery_id'],
            shipment_id=row['shipment_id'],
            courier=courier,
            status=DeliveryStatus(row['status']),
            estimated_arrival=row['estimated_arrival'],
            actual_arrival=row['actual_arrival']
        )

        delivery.created_at = row['created_at']
        delivery.updated_at = row['updated_at']

        return delivery
