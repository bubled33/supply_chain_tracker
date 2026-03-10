from typing import Optional, Protocol
from uuid import UUID

from datetime import datetime


class RefreshToken:
    token_id: UUID
    user_id: UUID
    token_hash: str
    expires_at: datetime
    revoked: bool
    created_at: datetime


class RefreshTokenRepositoryPort(Protocol):
    async def save(self, user_id: UUID, token_hash: str, expires_at: datetime) -> None: ...
    async def get_valid(self, token_hash: str) -> Optional["RefreshToken"]: ...
    async def revoke(self, token_hash: str) -> None: ...
