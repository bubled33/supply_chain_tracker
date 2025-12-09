import signal
import sys

import uvicorn
from fastapi import FastAPI
from libs.middlewares.logger import HttpLoggingMiddleware

from libs.observability.logger import (
    set_service_name,
    set_environment,
    get_json_logger,
)
from libs.observability.metrics import PrometheusMiddleware, metrics_endpoint

from api.router import router

SERVICE_NAME = "delivery_service"

app = FastAPI()
app.include_router(router)
app.add_middleware(
    HttpLoggingMiddleware,
    service_name="delivery_service",
    log_request_body=False,
    log_response_body=False,
)
app.add_middleware(PrometheusMiddleware, service_name=SERVICE_NAME)
app.add_api_route("/metrics", metrics_endpoint, methods=["GET"])

set_service_name("delivery_service")
set_environment("dev")
logger = get_json_logger("delivery_service")


def _handle_stop_signal(signum, frame):
    logger.info("service_stopping", extra={"signal": signum})
    sys.exit(0)


if __name__ == "__main__":
    logger.info(
        "service_starting",
        extra={
            "host": "0.0.0.0",
            "port": 8000,
        },
    )

    signal.signal(signal.SIGTERM, _handle_stop_signal)
    signal.signal(signal.SIGINT, _handle_stop_signal)

    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        logger.exception("service_crashed", extra={"error": str(e)})
        raise
    finally:
        logger.info("service_stopped")
