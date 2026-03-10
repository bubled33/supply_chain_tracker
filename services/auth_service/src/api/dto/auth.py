from uuid import UUID

from pydantic import BaseModel


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str = "operator"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class MeResponse(BaseModel):
    user_id: UUID
    username: str
    email: str
    role: str
    is_active: bool
