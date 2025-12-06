from fastapi import APIRouter

from src.api.handlers import items_router, shipments_router

router = APIRouter(prefix="/api/v1")
router.include_router(items_router)
router.include_router(shipments_router)