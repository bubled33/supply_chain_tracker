import asyncpg
from fastapi import Depends

from libs.deps.postgres_pool import PostgresPoolProvider
from libs.deps.queue import EventQueueProvider
from libs.auth import JWTAuthProvider

from src.config import settings
from src.app.services.item import ItemService
from src.app.services.shipment import ShipmentService
from src.infra.db.item_repository import AsyncPostgresItemRepository
from src.infra.db.shipment_repository import PostgresShipmentRepository


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


async def get_item_repository(
    pool: asyncpg.Pool = Depends(db_provider)
) -> AsyncPostgresItemRepository:
    return AsyncPostgresItemRepository(pool)


async def get_shipment_repository(
    pool: asyncpg.Pool = Depends(db_provider)
) -> PostgresShipmentRepository:
    return PostgresShipmentRepository(pool)


async def get_item_service(
    repository: AsyncPostgresItemRepository = Depends(get_item_repository)
) -> ItemService:
    return ItemService(repository=repository)


async def get_shipment_service(
    repository: PostgresShipmentRepository = Depends(get_shipment_repository)
) -> ShipmentService:
    return ShipmentService(repository=repository)
