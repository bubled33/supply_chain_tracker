import asyncio
from typing import List
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from .checks import HealthCheck
from .dto import HealthResponse, HealthStatus, ComponentHealth


def create_health_router(
        service_name: str,
        checks: List[HealthCheck]
) -> APIRouter:
    """Создаёт роутер с health endpoints."""

    router = APIRouter(tags=["Health"])

    @router.get(
        "/health",
        status_code=status.HTTP_200_OK,
        summary="Liveness probe - проверка работы сервиса"
    )
    async def health():
        """
        Простая проверка что сервис жив.
        Используется для Kubernetes liveness probe.
        """
        response = HealthResponse(
            service=service_name,
            status=HealthStatus.HEALTHY
        )
        return response.to_dict()

    @router.get(
        "/ready",
        summary="Readiness probe - готовность к приёму трафика"
    )
    async def ready():
        """
        Проверяет все зависимости (БД, Kafka, Redis).
        Используется для Kubernetes readiness probe.
        """
        components = {}
        overall_status = HealthStatus.HEALTHY

        # Параллельный запуск всех проверок
        results = await asyncio.gather(
            *[check.check() for check in checks],
            return_exceptions=True
        )

        for check, result in zip(checks, results):
            if isinstance(result, Exception):
                components[check.name] = ComponentHealth(
                    status=HealthStatus.UNHEALTHY,
                    details={"error": str(result)}
                )
                overall_status = HealthStatus.UNHEALTHY
            else:
                components[check.name] = result
                if result.status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif result.status == HealthStatus.DEGRADED and overall_status != HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.DEGRADED

        response = HealthResponse(
            service=service_name,
            status=overall_status,
            components=components
        )

        # Возвращаем 503 если не готовы
        if overall_status == HealthStatus.UNHEALTHY:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=response.to_dict()
            )

        return response.to_dict()

    return router
