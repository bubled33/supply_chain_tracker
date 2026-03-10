from typing import Optional
from uuid import UUID

import asyncpg

from src.domain.entities.user import User
from src.domain.ports.user_repository import UserRepositoryPort


class AsyncPostgresUserRepository(UserRepositoryPort):
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    def _row_to_entity(self, row: asyncpg.Record) -> User:
        return User(
            user_id=row["user_id"],
            username=row["username"],
            email=row["email"],
            hashed_password=row["hashed_password"],
            role=row["role"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def save(self, user: User) -> User:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO users (user_id, username, email, hashed_password, role, is_active, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    email = EXCLUDED.email,
                    hashed_password = EXCLUDED.hashed_password,
                    role = EXCLUDED.role,
                    is_active = EXCLUDED.is_active,
                    updated_at = EXCLUDED.updated_at
                RETURNING *
                """,
                user.user_id,
                user.username,
                user.email,
                user.hashed_password,
                user.role,
                user.is_active,
                user.created_at,
                user.updated_at,
            )
        return self._row_to_entity(row)

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        return self._row_to_entity(row) if row else None

    async def get_by_username(self, username: str) -> Optional[User]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE username = $1", username)
        return self._row_to_entity(row) if row else None

    async def get_by_email(self, email: str) -> Optional[User]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
        return self._row_to_entity(row) if row else None
