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
from src.app.services.shipment import ShipmentService
from src.app.workers.command_worker import ShipmentCommandWorker
from src.config import settings
from src.domain.errors import ShipmentNotFoundError
from src.infra.db.shipment_repository import PostgresShipmentRepository

set_service_name(settings.SERVICE_NAME)
set_environment(settings.ENVIRONMENT)
logger = get_json_logger(settings.SERVICE_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Shipment Service...")

    await db_provider.startup()
    await event_queue_provider.startup()

    shipment_repo = PostgresShipmentRepository(db_provider._pool)
    shipment_service = ShipmentService(repository=shipment_repo)
    command_worker = ShipmentCommandWorker(
        event_queue=event_queue_provider._adapter,
        shipment_service=shipment_service,
    )

    worker_task = asyncio.create_task(command_worker.run(), name="shipment_command_worker")

    logger.info(f"Service '{settings.SERVICE_NAME}' ready on port {settings.PORT}.")
    yield

    logger.info("Shutting down Shipment Service...")
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
        title="Shipment Service API",
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

    @app.exception_handler(ShipmentNotFoundError)
    async def handle_shipment_not_found(request: Request, exc: ShipmentNotFoundError) -> JSONResponse:
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
