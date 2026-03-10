import asyncio

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from libs.middlewares.logger import HttpLoggingMiddleware
from libs.observability.logger import set_service_name, set_environment, get_json_logger
from libs.observability.metrics import PrometheusMiddleware, metrics_endpoint

from src.api.router import router
from src.api.deps.getters import db_provider, event_queue_provider
from src.app.services.inventory_record import InventoryService
from src.app.workers.command_worker import WarehouseCommandWorker
from src.config import settings
from src.domain.errors.warehouse import WarehouseNotFoundError, WarehouseAlreadyExistsError
from src.domain.errors.inventory_record import InventoryRecordNotFoundError
from src.infra.db.inventory_repository import AsyncPostgresInventoryRepository

set_service_name(settings.SERVICE_NAME)
set_environment(settings.ENVIRONMENT)
logger = get_json_logger(settings.SERVICE_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Warehouse Service...")

    await db_provider.startup()
    await event_queue_provider.startup()

    inventory_repo = AsyncPostgresInventoryRepository(db_provider._pool)
    inventory_service = InventoryService(repository=inventory_repo)
    command_worker = WarehouseCommandWorker(
        event_queue=event_queue_provider._adapter,
        inventory_service=inventory_service,
    )

    worker_task = asyncio.create_task(command_worker.run(), name="warehouse_command_worker")

    logger.info(f"Service '{settings.SERVICE_NAME}' ready on port {settings.PORT}.")
    yield

    logger.info("Shutting down Warehouse Service...")
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        logger.info("Command worker stopped gracefully.")

    await event_queue_provider.shutdown()
    await db_provider.shutdown()
    logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Warehouse Service API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.ENVIRONMENT in ("local", "development") else None,
        redoc_url=None,
    )

    app.include_router(router)

    app.add_middleware(
        HttpLoggingMiddleware,
        service_name=settings.SERVICE_NAME,
        log_request_body=False,
        log_response_body=False,
    )
    app.add_middleware(PrometheusMiddleware, service_name=settings.SERVICE_NAME)
    app.add_api_route("/metrics", metrics_endpoint, methods=["GET"])

    @app.exception_handler(WarehouseNotFoundError)
    async def handle_warehouse_not_found(request: Request, exc: WarehouseNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(WarehouseAlreadyExistsError)
    async def handle_warehouse_already_exists(request: Request, exc: WarehouseAlreadyExistsError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(InventoryRecordNotFoundError)
    async def handle_inventory_not_found(request: Request, exc: InventoryRecordNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

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
