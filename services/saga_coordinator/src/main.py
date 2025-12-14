# src/main.py

import asyncio
import uvicorn
import asyncpg
from contextlib import asynccontextmanager
from fastapi import FastAPI

from libs.observability.logger import get_json_logger, set_service_name, set_environment
from libs.messaging.memory import InMemoryEventQueueAdapter
# from libs.messaging.kafka import KafkaEventQueueAdapter

from src.config import settings
from src.infra.db.saga_instance import AsyncPostgresSagaRepository
from src.app.services.saga_instance import SagaService
from src.app.workers.compensation_worker import SagaCompensationWorker

# Импортируем роутер и провайдеры зависимостей для инъекции пула
from src.api.router import router
from src.api.deps.getters import db_provider, event_queue_provider

# Настройка логгера
set_service_name(settings.SERVICE_NAME)
set_environment(settings.ENVIRONMENT)
logger = get_json_logger(settings.SERVICE_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения:
    - Подключение к БД и Брокеру
    - Инициализация сервисов
    - Запуск фоновых воркеров
    """
    logger.info("Starting Saga Coordinator Service...")

    # 1. Инициализация ресурсов (DB & Queue)
    try:
        pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=settings.DB_POOL_MIN_SIZE,
            max_size=settings.DB_POOL_MAX_SIZE
        )
        # ВАЖНО: Инъекция пула в провайдер зависимостей, чтобы API (Depends) мог его использовать
        # Предполагаем, что у PostgresPoolProvider есть атрибут pool или метод set_pool
        if hasattr(db_provider, "pool"):
            db_provider.pool = pool

        logger.info("Connected to PostgreSQL")
    except Exception as e:
        logger.critical(f"Failed to connect to database: {e}", exc_info=True)
        raise e

    event_queue = InMemoryEventQueueAdapter(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA_GROUP_ID
    )
    # Инъекция очереди в провайдер для API
    if hasattr(event_queue_provider, "queue"):
        event_queue_provider.queue = event_queue

    # 2. Инициализация бизнес-логики
    saga_repo = AsyncPostgresSagaRepository(pool=pool)
    saga_service = SagaService(repository=saga_repo)

    compensation_worker = SagaCompensationWorker(
        event_queue=event_queue,
        saga_service=saga_service
    )

    # 3. Запуск воркеров и очереди
    async with event_queue:
        logger.info("Event Queue Adapter started")

        # Запускаем воркер как фоновую задачу asyncio
        worker_task = asyncio.create_task(compensation_worker.run(), name="compensation_worker")

        logger.info(f"Service '{settings.SERVICE_NAME}' is ready to accept requests.")
        yield  # <-- Здесь приложение работает и принимает HTTP запросы

        # 4. Graceful Shutdown
        logger.info("Shutting down...")

        # Отменяем воркер
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            logger.info("Worker stopped gracefully")

    # 5. Закрытие соединения с БД
    logger.info("Closing database pool...")
    await pool.close()
    logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    """Фабрика создания приложения"""
    app = FastAPI(
        title="Saga Coordinator API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.ENVIRONMENT == "local" else None,
        redoc_url=None
    )

    # Регистрация роутеров
    app.include_router(router)

    return app


# Экземпляр приложения для uvicorn
app = create_app()

if __name__ == "__main__":
    # Запуск сервера
    # В продакшене лучше запускать через команду: uvicorn src.main:app --host 0.0.0.0 --port 8000
    try:
        import uvloop

        uvloop.install()
    except ImportError:
        pass

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=(settings.ENVIRONMENT == "local"),
        log_config=None  # Используем свой json логгер
    )
