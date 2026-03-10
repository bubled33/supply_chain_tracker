from dataclasses import dataclass
from uuid import UUID
from typing import Optional

@dataclass
class ItemCreateDTO:
    name: str
    quantity: int
    weight: float

@dataclass
class ItemDTO:
    item_id: UUID
    shipment_id: UUID
    name: str
    quantity: int
    weight: float

@dataclass
class ItemUpdateDTO:
    name: Optional[str] = None
    quantity: Optional[int] = None
    weight: Optional[float] = None
