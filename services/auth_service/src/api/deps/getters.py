import asyncpg
from fastapi import Depends

from libs.auth import JWTAuthProvider
from libs.deps.postgres_pool import PostgresPoolProvider

from src.config import settings
from src.infra.db.user_repository import AsyncPostgresUserRepository
from src.infra.db.refresh_token_repository import AsyncPostgresRefreshTokenRepository
from src.app.services.auth import AuthService

db_provider = PostgresPoolProvider(
    dsn=settings.DATABASE_URL,
    min_size=settings.DB_POOL_MIN_SIZE,
    max_size=settings.DB_POOL_MAX_SIZE,
)

auth_provider = JWTAuthProvider(
    secret_key=settings.JWT_SECRET_KEY,
    algorithm=settings.JWT_ALGORITHM,
    stateless=True,
)

get_current_user = auth_provider()


async def get_user_repository(
    pool: asyncpg.Pool = Depends(db_provider),
) -> AsyncPostgresUserRepository:
    return AsyncPostgresUserRepository(pool)


async def get_refresh_token_repository(
    pool: asyncpg.Pool = Depends(db_provider),
) -> AsyncPostgresRefreshTokenRepository:
    return AsyncPostgresRefreshTokenRepository(pool)


async def get_auth_service(
    user_repo: AsyncPostgresUserRepository = Depends(get_user_repository),
    token_repo: AsyncPostgresRefreshTokenRepository = Depends(get_refresh_token_repository),
) -> AuthService:
    return AuthService(user_repo=user_repo, token_repo=token_repo)
