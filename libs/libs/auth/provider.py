from typing import Callable, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from .jwt import verify_password, decode_token
from .models import UserInDB


class JWTAuthProvider:

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        token_url: str = "/api/v1/auth/token",
        users: Optional[dict] = None,
        stateless: bool = False,
    ):
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._token_url = token_url
        self._users: dict[str, UserInDB] = users or {}
        self._stateless = stateless

    def authenticate(self, username: str, password: str) -> Optional[UserInDB]:
        user = self._users.get(username)
        if user and verify_password(password, user.hashed_password):
            return user
        return None

    def __call__(self) -> Callable:
        provider = self
        oauth2_scheme = OAuth2PasswordBearer(tokenUrl=self._token_url)

        async def _get_current_user(
            token: str = Depends(oauth2_scheme),
        ) -> UserInDB:
            credentials_exception = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            try:
                payload = decode_token(token, provider._secret_key, provider._algorithm)
                username: str = payload.sub
                if username is None:
                    raise credentials_exception
            except JWTError:
                raise credentials_exception

            if provider._stateless:
                return UserInDB(username=username, hashed_password="", role=payload.role)

            user = provider._users.get(username)
            if user is None:
                raise credentials_exception
            return user

        return _get_current_user


def require_role(*allowed_roles: str, current_user_dep: Callable):
    def _check(current_user: UserInDB = Depends(current_user_dep)):
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return current_user
    return _check
