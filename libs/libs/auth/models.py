from dataclasses import dataclass, field


@dataclass(frozen=True)
class UserInDB:
    username: str
    hashed_password: str
    role: str = "operator"


@dataclass(frozen=True)
class TokenPayload:
    sub: str
    exp: int
    role: str = "operator"
