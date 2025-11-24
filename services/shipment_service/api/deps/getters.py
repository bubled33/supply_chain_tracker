from typing import AsyncIterator
from functools import lru_cache
from fastapi import Depends
import asyncpg

from libs.messaging.memory import InMemoryEventQueueAdapter
from services.shipment_service.app.services.item import ItemService
from services.shipment_service.app.services.shipment import ShipmentService
from services.shipment_service.infra.db.item_repository import (
    AsyncPostgresItemRepository
)
from services.shipment_service.infra.db.shipment_repository import (
    PostgresShipmentRepository
)
from libs.messaging.ports import EventQueuePort

# from libs.messaging.adapters.kafka_adapter import KafkaEventQueueAdapter
# from config import settings


# ---- Database Connection Pool ----

_db_pool: asyncpg.Pool | None = None


async def get_db_pool() -> asyncpg.Pool:
    """
    Получить или создать connection pool для PostgreSQL.
    Singleton pattern для переиспользования пула.
    """
    global _db_pool

    if _db_pool is None:
        _db_pool = await asyncpg.create_pool(
            host="localhost",
            port=5432,
            database="supply_chain",
            user="bubled",
            password=***REMOVED***
            min_size=5,
            max_size=20,
            command_timeout=60,
        )
        print("[INFO] PostgreSQL connection pool created")

    return _db_pool


async def close_db_pool():
    """Закрыть connection pool при shutdown приложения"""
    global _db_pool

    if _db_pool is not None:
        await _db_pool.close()
        _db_pool = None
        print("[INFO] PostgreSQL connection pool closed")


# ---- Repositories ----

async def get_item_repository():
    """Dependency для Item Repository"""
    pool = await get_db_pool()
    return AsyncPostgresItemRepository(pool)


async def get_shipment_repository():
    """Dependency для Shipment Repository"""
    pool = await get_db_pool()
    return PostgresShipmentRepository(pool)


# ---- Services ----

async def get_item_service(
        repository: AsyncPostgresItemRepository = Depends(get_item_repository)
) -> ItemService:
    """Dependency для Item Service с инъекцией репозитория"""
    return ItemService(repository=repository)


async def get_shipment_service(
        repository: PostgresShipmentRepository = Depends(get_shipment_repository)
) -> ShipmentService:
    """Dependency для Shipment Service с инъекцией репозитория"""
    return ShipmentService(repository=repository)


# ---- Event Queue ----

# Singleton для In-Memory adapter (переиспользуем экземпляр)
@lru_cache
def _get_event_queue_adapter() -> InMemoryEventQueueAdapter:
    """Создать единственный экземпляр In-Memory adapter"""
    return InMemoryEventQueueAdapter(
        bootstrap_servers="mock",
        group_id="shipment-service",
    )


# # Singleton для Kafka producer (переиспользуем соединение)
# @lru_cache
# def _get_kafka_adapter() -> KafkaEventQueueAdapter:
#     """Создать единственный экземпляр Kafka adapter"""
#     return KafkaEventQueueAdapter(
#         bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
#         group_id=settings.KAFKA_GROUP_ID or "shipment-service",
#     )


async def get_event_queue() -> AsyncIterator[EventQueuePort]:
    """
    Dependency для FastAPI с lifecycle management.
    Использует In-Memory adapter для разработки/тестирования.
    """
    adapter = _get_event_queue_adapter()

    # Инициализируем producer (mock)
    await adapter._get_producer()

    try:
        yield adapter
    finally:
        # Cleanup происходит при shutdown приложения
        pass


# async def get_event_queue() -> AsyncIterator[EventQueuePort]:
#     """
#     Dependency для FastAPI с lifecycle management.
#     Инициализирует producer при первом использовании.
#     """
#     adapter = _get_kafka_adapter()
#
#     # Инициализируем producer (если ещё не создан)
#     await adapter._get_producer()
#
#     try:
#         yield adapter
#     finally:
#         # Cleanup происходит при shutdown приложения
#         pass


# Альтернатива: без singleton (новое соединение каждый раз)
async def get_event_queue_isolated() -> AsyncIterator[EventQueuePort]:
    """
    Dependency с изолированным соединением.
    Создаёт новое соединение для каждого запроса.
    """
    # In-Memory версия
    adapter = InMemoryEventQueueAdapter(
        bootstrap_servers="mock",
        group_id="shipment-service",
    )

    # # Kafka версия
    # adapter = KafkaEventQueueAdapter(
    #     bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    #     group_id="shipment-service",
    # )

    try:
        yield adapter
    finally:
        # Закрываем соединение после использования
        await adapter.close()
