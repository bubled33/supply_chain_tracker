from dataclasses import dataclass
from uuid import UUID
from typing import Optional


@dataclass
class WarehouseCreateDTO:
    """DTO для создания нового склада."""
    name: str
    country: str
    city: str
    address: str = ""


@dataclass
class WarehouseDTO:
    """DTO для ответа API / представления склада."""
    warehouse_id: UUID
    name: str
    country: str
    city: str
    address: str


@dataclass
class WarehouseUpdateDTO:
    """
    DTO для обновления данных склада.
    """
    name: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
