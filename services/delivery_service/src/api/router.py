from fastapi import APIRouter

from src.api.handlers.courier import courier_router
from src.api.handlers.delivery import delivery_router

router = APIRouter(prefix="/api/v1")
router.include_router(courier_router)
router.include_router(delivery_router)