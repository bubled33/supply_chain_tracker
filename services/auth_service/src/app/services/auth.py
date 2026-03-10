import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from libs.auth.jwt import hash_password, verify_password, create_access_token

from src.config import settings
from src.domain.entities.user import User
from src.domain.errors.auth import UserAlreadyExistsError, InvalidCredentialsError, UserNotFoundError
from src.domain.ports.user_repository import UserRepositoryPort
from src.domain.ports.refresh_token_repository import RefreshTokenRepositoryPort


class AuthService:
    def __init__(
        self,
        user_repo: UserRepositoryPort,
        token_repo: RefreshTokenRepositoryPort,
    ):
        self._user_repo = user_repo
        self._token_repo = token_repo

    async def register(self, username: str, email: str, password: str, role: str = "operator") -> User:
        if await self._user_repo.get_by_username(username):
            raise UserAlreadyExistsError(f"Username '{username}' already exists")
        if await self._user_repo.get_by_email(email):
            raise UserAlreadyExistsError(f"Email '{email}' already exists")

        now = datetime.now(timezone.utc)
        user = User(
            user_id=uuid4(),
            username=username,
            email=email,
            hashed_password=hash_password(password),
            role=role,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        return await self._user_repo.save(user)

    async def authenticate(self, username: str, password: str) -> User:
        user = await self._user_repo.get_by_username(username)
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Invalid username or password")
        return user

    def create_access_token(self, user: User) -> str:
        return create_access_token(
            data={"sub": user.username, "role": user.role},
            secret_key=settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
            expires_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        )

    async def create_refresh_token(self, user: User) -> str:
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self._token_repo.save(user.user_id, token_hash, expires_at)
        return raw_token

    async def refresh(self, raw_token: str) -> tuple[str, str]:
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        record = await self._token_repo.get_valid(token_hash)
        if record is None:
            raise InvalidCredentialsError("Invalid or expired refresh token")

        await self._token_repo.revoke(token_hash)

        user = await self._user_repo.get_by_id(record.user_id)
        if not user:
            raise UserNotFoundError("User not found")

        new_access = self.create_access_token(user)
        new_refresh = await self.create_refresh_token(user)
        return new_access, new_refresh

    async def get_me(self, username: str) -> User:
        user = await self._user_repo.get_by_username(username)
        if not user:
            raise UserNotFoundError(f"User '{username}' not found")
        return user
