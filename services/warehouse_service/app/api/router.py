from fastapi import APIRouter

from app.api.handlers.inventory_record import inventory_router
from app.api.handlers.warehouse import warehouse_router

router = APIRouter(prefix="/api/v1")
router.include_router(warehouse_router)
router.include_router(inventory_router)