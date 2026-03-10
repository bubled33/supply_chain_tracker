import asyncio

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI

from libs.observability.logger import get_json_logger, set_service_name, set_environment

from src.config import settings
from src.infra.db.saga_instance import AsyncPostgresSagaRepository
from src.app.services.saga_instance import SagaService
from src.app.workers.compensation_worker import SagaCompensationWorker

from src.api.router import router
from src.api.deps.getters import db_provider, event_queue_provider

set_service_name(settings.SERVICE_NAME)
set_environment(settings.ENVIRONMENT)
logger = get_json_logger(settings.SERVICE_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Saga Coordinator Service...")

    await db_provider.startup()
    await event_queue_provider.startup()

    saga_repo = AsyncPostgresSagaRepository(pool=db_provider._pool)
    saga_service = SagaService(repository=saga_repo)

    compensation_worker = SagaCompensationWorker(
        event_queue=event_queue_provider._adapter,
        saga_service=saga_service,
    )

    worker_task = asyncio.create_task(compensation_worker.run(), name="compensation_worker")

    logger.info(f"Service '{settings.SERVICE_NAME}' ready on port {settings.PORT}.")
    yield

    logger.info("Shutting down Saga Coordinator...")
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        logger.info("Compensation worker stopped gracefully.")

    await event_queue_provider.shutdown()
    await db_provider.shutdown()
    logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Saga Coordinator API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.ENVIRONMENT in ("local", "development") else None,
        redoc_url=None,
    )

    app.include_router(router)

    return app


app = create_app()

if __name__ == "__main__":
    try:
        import uvloop
        uvloop.install()
    except ImportError:
        pass

    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=(settings.ENVIRONMENT == "local"),
        log_config=None,
    )
