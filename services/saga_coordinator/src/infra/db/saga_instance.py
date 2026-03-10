from typing import List, Optional
from uuid import UUID
import asyncpg
from datetime import datetime, timezone

from src.domain.entities.saga_instance import SagaInstance, SagaStatus
from src.domain.ports.saga_instance_repository import SagaRepositoryPort


class AsyncPostgresSagaRepository(SagaRepositoryPort):
    """Асинхронный репозиторий для SagaInstance на базе PostgreSQL"""

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def save(self, saga: SagaInstance) -> SagaInstance:
        """UPSERT для саги: создает новую или обновляет существующую"""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO saga_instances (
                    saga_id, saga_type, shipment_id, warehouse_id, delivery_id,
                    status, started_at, updated_at, failed_step, error_message
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (saga_id)
                DO UPDATE SET
                    warehouse_id = EXCLUDED.warehouse_id,
                    delivery_id = EXCLUDED.delivery_id,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at,
                    failed_step = EXCLUDED.failed_step,
                    error_message = EXCLUDED.error_message
                RETURNING 
                    saga_id, saga_type, shipment_id, warehouse_id, delivery_id,
                    status, started_at, updated_at, failed_step, error_message
            """,
                saga.saga_id,
                saga.saga_type,
                saga.shipment_id,
                saga.warehouse_id,
                saga.delivery_id,
                saga.status.value,  # Enum -> str
                saga.started_at,
                saga.updated_at,
                saga.failed_step,
                saga.error_message
            )

            return self._row_to_entity(row)

    async def get(self, saga_id: UUID) -> Optional[SagaInstance]:
        """Получить сагу по ID"""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT 
                    saga_id, saga_type, shipment_id, warehouse_id, delivery_id,
                    status, started_at, updated_at, failed_step, error_message
                FROM saga_instances
                WHERE saga_id = $1
            """, saga_id)

            return self._row_to_entity(row) if row else None

    async def get_by_shipment(self, shipment_id: UUID) -> Optional[SagaInstance]:
        """Получить сагу по ID отправления (предполагаем 1 к 1 для активных процессов)"""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT 
                    saga_id, saga_type, shipment_id, warehouse_id, delivery_id,
                    status, started_at, updated_at, failed_step, error_message
                FROM saga_instances
                WHERE shipment_id = $1
                ORDER BY started_at DESC
                LIMIT 1
            """, shipment_id)

            return self._row_to_entity(row) if row else None

    async def list_active(self) -> List[SagaInstance]:
        """Получить список всех незавершенных саг (для восстановления после сбоев)"""
        async with self._pool.acquire() as conn:
            # Ищем саги, которые "зависли" или в процессе компенсации
            rows = await conn.fetch("""
                SELECT 
                    saga_id, saga_type, shipment_id, warehouse_id, delivery_id,
                    status, started_at, updated_at, failed_step, error_message
                FROM saga_instances
                WHERE status IN ($1, $2)
                ORDER BY updated_at ASC
            """, SagaStatus.STARTED.value, SagaStatus.COMPENSATING.value)

            return [self._row_to_entity(row) for row in rows]

    @staticmethod
    def _row_to_entity(row) -> SagaInstance:
        """Преобразовать row в entity"""
        return SagaInstance(
            saga_id=row['saga_id'],
            saga_type=row['saga_type'],
            shipment_id=row['shipment_id'],
            warehouse_id=row['warehouse_id'],
            delivery_id=row['delivery_id'],
            status=SagaStatus(row['status']),  # str -> Enum
            started_at=row['started_at'],
            updated_at=row['updated_at'],
            failed_step=row['failed_step'],
            error_message=row['error_message']
        )
