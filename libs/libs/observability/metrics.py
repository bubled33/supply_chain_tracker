# libs/observability/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from time import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# HTTP метрики
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["service", "method", "path", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency, seconds",
    ["service", "method", "path"],
    buckets=(0.01, 0.05, 0.1, 0.3, 0.5, 1, 2, 5),
)

class PrometheusMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, service_name: str):
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request: Request, call_next):
        start = time()
        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            # нормализуем path (можно резать path params)
            path = request.url.path
            method = request.method
            status = response.status_code if response else 500

            HTTP_REQUESTS_TOTAL.labels(
                service=self.service_name,
                method=method,
                path=path,
                status=status,
            ).inc()

            duration = time() - start
            HTTP_REQUEST_DURATION_SECONDS.labels(
                service=self.service_name,
                method=method,
                path=path,
            ).observe(duration)


async def metrics_endpoint():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
