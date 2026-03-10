import asyncpg
from fastapi import Depends

from libs.deps.postgres_pool import PostgresPoolProvider
from libs.deps.queue import EventQueueProvider
from libs.auth import JWTAuthProvider

from src.config import settings
from src.app.services.inventory_record import InventoryService
from src.app.services.warehouse import WarehouseService
from src.infra.db.inventory_repository import AsyncPostgresInventoryRepository
from src.infra.db.warehouse_repository import AsyncPostgresWarehouseRepository


event_queue_provider = EventQueueProvider(
    use_kafka=settings.USE_KAFKA,
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    group_id=settings.KAFKA_GROUP_ID,
)

db_provider = PostgresPoolProvider(
    dsn=settings.DATABASE_URL,
    min_size=settings.DB_POOL_MIN_SIZE,
    max_size=settings.DB_POOL_MAX_SIZE,
)

get_event_queue = event_queue_provider

auth_provider = JWTAuthProvider(
    secret_key=settings.JWT_SECRET_KEY,
    algorithm=settings.JWT_ALGORITHM,
    stateless=True,
)

get_current_user = auth_provider()


async def get_inventory_repository(
    pool: asyncpg.Pool = Depends(db_provider),
) -> AsyncPostgresInventoryRepository:
    return AsyncPostgresInventoryRepository(pool)


async def get_warehouse_repository(
    pool: asyncpg.Pool = Depends(db_provider),
) -> AsyncPostgresWarehouseRepository:
    return AsyncPostgresWarehouseRepository(pool)


async def get_inventory_service(
    repository: AsyncPostgresInventoryRepository = Depends(get_inventory_repository),
) -> InventoryService:
    return InventoryService(repository=repository)


async def get_warehouse_service(
    repository: AsyncPostgresWarehouseRepository = Depends(get_warehouse_repository),
) -> WarehouseService:
    return WarehouseService(repository=repository)
