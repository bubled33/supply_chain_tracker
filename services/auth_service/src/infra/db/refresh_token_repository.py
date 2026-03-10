from datetime import datetime
from typing import Optional
from uuid import UUID

import asyncpg

from src.domain.ports.refresh_token_repository import RefreshTokenRepositoryPort, RefreshToken


class AsyncPostgresRefreshTokenRepository(RefreshTokenRepositoryPort):
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def save(self, user_id: UUID, token_hash: str, expires_at: datetime) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
                VALUES ($1, $2, $3)
                """,
                user_id,
                token_hash,
                expires_at,
            )

    async def get_valid(self, token_hash: str) -> Optional[RefreshToken]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM refresh_tokens
                WHERE token_hash = $1 AND revoked = false AND expires_at > NOW()
                """,
                token_hash,
            )
        if not row:
            return None
        token = RefreshToken()
        token.token_id = row["token_id"]
        token.user_id = row["user_id"]
        token.token_hash = row["token_hash"]
        token.expires_at = row["expires_at"]
        token.revoked = row["revoked"]
        token.created_at = row["created_at"]
        return token

    async def revoke(self, token_hash: str) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE refresh_tokens SET revoked = true WHERE token_hash = $1",
                token_hash,
            )
