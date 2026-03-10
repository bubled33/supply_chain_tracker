import json
import logging
import sys
from datetime import datetime, timezone
from contextvars import ContextVar
from typing import Any, Dict, Optional

correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
service_name_var: ContextVar[Optional[str]] = ContextVar("service_name", default=None)
environment_var: ContextVar[Optional[str]] = ContextVar("environment", default="local")


def set_correlation_id(correlation_id: str) -> None:
    correlation_id_var.set(correlation_id)


def set_service_name(service_name: str) -> None:
    service_name_var.set(service_name)


def set_environment(env: str) -> None:
    environment_var.set(env)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        corr_id = correlation_id_var.get()
        if corr_id:
            payload["correlation_id"] = corr_id

        service = service_name_var.get()
        if service:
            payload["service"] = service

        env = environment_var.get()
        if env:
            payload["environment"] = env

        for key, value in record.__dict__.items():
            if key.startswith("_"):
                continue
            if key in (
                "name", "msg", "args", "levelname", "levelno",
                "pathname", "filename", "module", "exc_info",
                "exc_text", "stack_info", "lineno", "funcName",
                "created", "msecs", "relativeCreated", "thread",
                "threadName", "processName", "process",
            ):
                continue
            if key not in payload:
                payload[key] = value

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def get_json_logger(name: str = "app", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)

    logger.propagate = False

    return logger
