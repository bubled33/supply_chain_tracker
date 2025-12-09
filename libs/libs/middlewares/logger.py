# libs/observability/http_logging.py
from time import time
from typing import Callable, Awaitable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from libs.observability.logger import get_json_logger, set_service_name


class HttpLoggingMiddleware(BaseHTTPMiddleware):
    """
    Универсальная middleware для логирования HTTP-запросов.
    Логирует:
    - метод, путь, статус
    - время обработки
    - client_ip
    - опционально user-agent, query, body (по флагам)
    """

    def __init__(
        self,
        app: ASGIApp,
        service_name: str,
        log_request_body: bool = False,
        log_response_body: bool = False,
    ) -> None:
        super().__init__(app)
        self.service_name = service_name
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body

        set_service_name(service_name)
        self.logger = get_json_logger(service_name)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        start = time()

        # Базовая инфа о запросе
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Опционально читаем body (осторожно на больших запросах)
        body_text: str | None = None
        if self.log_request_body:
            try:
                body_bytes = await request.body()
                body_text = body_bytes.decode("utf-8") if body_bytes else None

                # нужно пересоздать запрос с тем же body, иначе downstream уже не прочитает
                async def receive():
                    return {"type": "http.request", "body": body_bytes, "more_body": False}

                request = Request(scope=request.scope, receive=receive)
            except Exception as e:
                self.logger.warning(
                    "request_body_read_failed",
                    extra={"error": str(e), "path": path},
                )

        self.logger.info(
            "http_request_started",
            extra={
                "method": method,
                "path": path,
                "client_ip": client_ip,
                "user_agent": user_agent,
            },
        )

        try:
            response = await call_next(request)
        except Exception as e:
            duration = time() - start
            self.logger.exception(
                "http_request_failed",
                extra={
                    "method": method,
                    "path": path,
                    "client_ip": client_ip,
                    "duration_ms": round(duration * 1000, 2),
                    "error": str(e),
                },
            )
            raise

        duration = time() - start

        # Опционально логируем body ответа
        resp_body_text: str | None = None
        if self.log_response_body:
            try:
                # Response может быть StreamingResponse, тогда лучше не лезть
                if hasattr(response, "body"):
                    body_bytes = response.body
                    if isinstance(body_bytes, (bytes, bytearray)):
                        resp_body_text = body_bytes.decode("utf-8")
            except Exception as e:
                self.logger.warning(
                    "response_body_read_failed",
                    extra={"error": str(e), "path": path},
                )

        self.logger.info(
            "http_request_finished",
            extra={
                "method": method,
                "path": path,
                "status": response.status_code,
                "client_ip": client_ip,
                "duration_ms": round(duration * 1000, 2),
                "request_body": body_text if self.log_request_body else None,
                "response_body": resp_body_text if self.log_response_body else None,
            },
        )

        return response
