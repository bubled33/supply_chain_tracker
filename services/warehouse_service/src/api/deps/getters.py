# warehouse_service/src/api/deps/getters.py
import os
import asyncpg
from fastapi import Depends

from libs.deps.postgres_pool import PostgresPoolProvider
from libs.deps.queue import EventQueueProvider

from src.app.services.inventory_record import InventoryService
from src.app.services.warehouse import WarehouseService
from src.infra.db.inventory_repository import AsyncPostgresInventoryRepository
from src.infra.db.warehouse_repository import AsyncPostgresWarehouseRepository

event_queue_provider = EventQueueProvider(
    use_kafka=os.getenv("USE_KAFKA", "false").lower() == "true",
    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
    group_id="warehouse-service",
)

db_provider = PostgresPoolProvider(
    dsn=os.getenv(
        "DATABASE_URL",
        "postgresql://***REMOVED***@localhost:5432/supply_chain",
    ),
    min_size=5,
    max_size=20,
)

get_event_queue = event_queue_provider


async def get_inventory_repository(
    pool: asyncpg.Pool = Depends(db_provider),
) -> AsyncPostgresInventoryRepository:
    """Dependency для Inventory Repository."""
    return AsyncPostgresInventoryRepository(pool)


async def get_warehouse_repository(
    pool: asyncpg.Pool = Depends(db_provider),
) -> AsyncPostgresWarehouseRepository:
    """Dependency для Warehouse Repository."""
    return AsyncPostgresWarehouseRepository(pool)


async def get_inventory_service(
    repository: AsyncPostgresInventoryRepository = Depends(get_inventory_repository),
) -> InventoryService:
    """Dependency для Inventory Service с инъекцией репозитория."""
    return InventoryService(repository=repository)


async def get_warehouse_service(
    repository: AsyncPostgresWarehouseRepository = Depends(get_warehouse_repository),
) -> WarehouseService:
    """Dependency для Warehouse Service с инъекцией репозитория."""
    return WarehouseService(repository=repository)
