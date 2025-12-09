# libs/logging/json_logger.py
import json
import logging
import sys
from datetime import datetime, timezone
from contextvars import ContextVar
from typing import Any, Dict, Optional

# Глобальный контекст для correlation_id и прочего
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
        # базовые поля
        payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # контекст из ContextVar
        corr_id = correlation_id_var.get()
        if corr_id:
            payload["correlation_id"] = corr_id

        service = service_name_var.get()
        if service:
            payload["service"] = service

        env = environment_var.get()
        if env:
            payload["environment"] = env

        # extra-поля (которые передаем через logger.info(..., extra={...}))
        for key, value in record.__dict__.items():
            if key.startswith("_"):
                continue
            # пропускаем стандартные поля logging
            if key in (
                "name", "msg", "args", "levelname", "levelno",
                "pathname", "filename", "module", "exc_info",
                "exc_text", "stack_info", "lineno", "funcName",
                "created", "msecs", "relativeCreated", "thread",
                "threadName", "processName", "process",
            ):
                continue
            # добавляем в payload
            if key not in payload:
                payload[key] = value

        # exception / stacktrace
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def get_json_logger(name: str = "app", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # чтобы не плодить хендлеры при повторных вызовах
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)

    # не пускать логи дальше наверх к root, чтобы не дублировать
    logger.propagate = False

    return logger
