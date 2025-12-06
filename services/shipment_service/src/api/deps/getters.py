import os
import asyncpg
from fastapi import Depends

# Импорты провайдеров из libs
from libs.deps.postgres_pool import PostgresPoolProvider
from libs.deps.queue import EventQueueProvider


# Импорты сервисов
from src.app.services.item import ItemService
from src.app.services.shipment import ShipmentService
from src.infra.db.item_repository import AsyncPostgresItemRepository
from src.infra.db.shipment_repository import PostgresShipmentRepository

# ---- Config & Providers Instances ----

# Провайдер для очереди событий
event_queue_provider = EventQueueProvider(
    use_kafka=os.getenv("USE_KAFKA", "false").lower() == "true",
    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
    group_id="shipment-service"
)

# Провайдер для пула БД
db_provider = PostgresPoolProvider(
    dsn=os.getenv("DATABASE_URL", "postgresql://***REMOVED***@localhost:5432/supply_chain"),
    min_size=5,
    max_size=20
)

# Алиас для использования очереди как зависимости
get_event_queue = event_queue_provider


# ---- Repositories ----

async def get_item_repository(
    pool: asyncpg.Pool = Depends(db_provider)
) -> AsyncPostgresItemRepository:
    """Dependency для Item Repository"""
    return AsyncPostgresItemRepository(pool)


async def get_shipment_repository(
    pool: asyncpg.Pool = Depends(db_provider)
) -> PostgresShipmentRepository:
    """Dependency для Shipment Repository"""
    return PostgresShipmentRepository(pool)


# ---- Services ----

async def get_item_service(
    repository: AsyncPostgresItemRepository = Depends(get_item_repository)
) -> ItemService:
    """Dependency для Item Service"""
    return ItemService(repository=repository)


async def get_shipment_service(
    repository: PostgresShipmentRepository = Depends(get_shipment_repository)
) -> ShipmentService:
    """Dependency для Shipment Service"""
    return ShipmentService(repository=repository)
