import asyncpg
from fastapi import Depends

from libs.deps.postgres_pool import PostgresPoolProvider
from libs.deps.queue import EventQueueProvider
from libs.auth import JWTAuthProvider

from src.config import settings
from src.infra.db.courier_repository import (
    AsyncPostgresCourierRepository
)
from src.infra.db.delivery_repository import (
    AsyncPostgresDeliveryRepository
)

from src.app.services.courier import CourierService
from src.app.services.delivery import DeliveryService

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


async def get_courier_repository(
    pool: asyncpg.Pool = Depends(db_provider)
) -> AsyncPostgresCourierRepository:
    return AsyncPostgresCourierRepository(pool)


async def get_delivery_repository(
    pool: asyncpg.Pool = Depends(db_provider)
) -> AsyncPostgresDeliveryRepository:
    return AsyncPostgresDeliveryRepository(pool)


async def get_courier_service(
    repository: AsyncPostgresCourierRepository = Depends(get_courier_repository)
) -> CourierService:
    return CourierService(repository=repository)


async def get_delivery_service(
    repository: AsyncPostgresDeliveryRepository = Depends(get_delivery_repository)
) -> DeliveryService:
    return DeliveryService(repository=repository)
