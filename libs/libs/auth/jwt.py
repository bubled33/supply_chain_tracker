from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt as jose_jwt

from .models import TokenPayload


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()


def create_access_token(
    data: dict,
    secret_key: str,
    algorithm: str = "HS256",
    expires_minutes: int = 60,
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jose_jwt.encode(to_encode, secret_key, algorithm=algorithm)


def decode_token(token: str, secret_key: str, algorithm: str = "HS256") -> TokenPayload:
    payload = jose_jwt.decode(token, secret_key, algorithms=[algorithm])
    return TokenPayload(sub=payload["sub"], exp=int(payload["exp"]), role=payload.get("role", "operator"))
