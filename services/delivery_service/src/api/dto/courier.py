from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field


class CourierCreateDTO(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, examples=["John Doe"])
    contact_info: str = Field(..., min_length=5, examples=["Phone: +7-999-000-11-22"])


class CourierDTO(BaseModel):
    courier_id: UUID
    name: str
    contact_info: str

    model_config = {"from_attributes": True}


class CourierUpdateDTO(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    contact_info: Optional[str] = Field(None, min_length=5)
