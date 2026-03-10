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
from src.app.services.delivery import DeliveryService
from src.app.workers.command_worker import DeliveryCommandWorker
from src.config import settings
from src.domain.errors.courier import CourierNotFoundError, CourierAlreadyExistsError
from src.domain.errors.delivery import DeliveryNotFoundError
from src.infra.db.delivery_repository import AsyncPostgresDeliveryRepository

set_service_name(settings.SERVICE_NAME)
set_environment(settings.ENVIRONMENT)
logger = get_json_logger(settings.SERVICE_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Delivery Service...")

    await db_provider.startup()
    await event_queue_provider.startup()

    delivery_repo = AsyncPostgresDeliveryRepository(db_provider._pool)
    delivery_service = DeliveryService(repository=delivery_repo)
    command_worker = DeliveryCommandWorker(
        event_queue=event_queue_provider._adapter,
        delivery_service=delivery_service,
    )

    worker_task = asyncio.create_task(command_worker.run(), name="delivery_command_worker")

    logger.info(f"Service '{settings.SERVICE_NAME}' ready on port {settings.PORT}.")
    yield

    logger.info("Shutting down Delivery Service...")
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
        title="Delivery Service API",
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

    @app.exception_handler(CourierNotFoundError)
    async def handle_courier_not_found(request: Request, exc: CourierNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(CourierAlreadyExistsError)
    async def handle_courier_already_exists(request: Request, exc: CourierAlreadyExistsError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(DeliveryNotFoundError)
    async def handle_delivery_not_found(request: Request, exc: DeliveryNotFoundError) -> JSONResponse:
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
