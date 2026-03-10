from fastapi import APIRouter

from libs.health.router import create_health_router
from src.api.handlers import items_router, shipments_router
from src.config import settings

health_router = create_health_router(
    service_name=settings.SERVICE_NAME,
    checks=[],
)

router = APIRouter(prefix="/api/v1")
router.include_router(health_router)
router.include_router(items_router)
router.include_router(shipments_router)
