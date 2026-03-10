from fastapi import APIRouter

from src.api.handlers.auth import auth_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
