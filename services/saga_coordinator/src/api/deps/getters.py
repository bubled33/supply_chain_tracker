import asyncpg
from fastapi import Depends

from libs.deps.postgres_pool import PostgresPoolProvider
from libs.deps.queue import EventQueueProvider

from src.config import settings
from src.infra.db.saga_instance import AsyncPostgresSagaRepository
from src.app.services.saga_instance import SagaService

use_kafka = settings.ENVIRONMENT.lower() != "local"

event_queue_provider = EventQueueProvider(
    use_kafka=use_kafka,
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    group_id=settings.KAFKA_GROUP_ID
)

db_provider = PostgresPoolProvider(
    dsn=settings.DATABASE_URL,
    min_size=settings.DB_POOL_MIN_SIZE,
    max_size=settings.DB_POOL_MAX_SIZE
)

get_event_queue = event_queue_provider

async def get_saga_repository(
    pool: asyncpg.Pool = Depends(db_provider)
) -> AsyncPostgresSagaRepository:
    """Dependency для Saga Repository"""
    return AsyncPostgresSagaRepository(pool)

async def get_saga_service(
    repository: AsyncPostgresSagaRepository = Depends(get_saga_repository)
) -> SagaService:
    """Dependency для Saga Service с инъекцией репозитория"""
    return SagaService(repository=repository)
