from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class User:
    user_id: UUID
    username: str
    email: str
    hashed_password: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
