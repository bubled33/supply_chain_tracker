import os
import asyncpg
from fastapi import Depends

from libs.deps.postgres_pool import PostgresPoolProvider
from libs.deps.queue import EventQueueProvider

from src.infra.db.courier_repository import (
    AsyncPostgresCourierRepository
)
from src.infra.db.delivery_repository import (
    AsyncPostgresDeliveryRepository
)

from src.app.services.courier import CourierService
from src.app.services.delivery import DeliveryService

event_queue_provider = EventQueueProvider(
    use_kafka=os.getenv("USE_KAFKA", "false").lower() == "true",
    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
    group_id="delivery-service"
)

db_provider = PostgresPoolProvider(
    dsn=os.getenv("DATABASE_URL", "postgresql://***REMOVED***@localhost:5432/supply_chain"),
    min_size=5,
    max_size=20
)

get_event_queue = event_queue_provider

async def get_courier_repository(
    pool: asyncpg.Pool = Depends(db_provider)
) -> AsyncPostgresCourierRepository:
    """Dependency для Courier Repository"""
    return AsyncPostgresCourierRepository(pool)


async def get_delivery_repository(
    pool: asyncpg.Pool = Depends(db_provider)
) -> AsyncPostgresDeliveryRepository:
    """Dependency для Delivery Repository"""
    return AsyncPostgresDeliveryRepository(pool)

async def get_courier_service(
    repository: AsyncPostgresCourierRepository = Depends(get_courier_repository)
) -> CourierService:
    """Dependency для Courier Service с инъекцией репозитория"""
    return CourierService(repository=repository)


async def get_delivery_service(
    repository: AsyncPostgresDeliveryRepository = Depends(get_delivery_repository)
) -> DeliveryService:
    """Dependency для Delivery Service с инъекцией репозитория"""
    return DeliveryService(repository=repository)
