from fastapi import APIRouter

from .handlers.saga_instance import saga_router

router = APIRouter(prefix="/api/v1")

router.include_router(saga_router)