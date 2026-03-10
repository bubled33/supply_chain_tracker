from dataclasses import dataclass
from uuid import UUID
from typing import Optional


@dataclass
class WarehouseCreateDTO:
    name: str
    country: str
    city: str
    address: str = ""


@dataclass
class WarehouseDTO:
    warehouse_id: UUID
    name: str
    country: str
    city: str
    address: str


@dataclass
class WarehouseUpdateDTO:
    name: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
