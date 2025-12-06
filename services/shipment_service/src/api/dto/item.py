from dataclasses import dataclass
from uuid import UUID
from typing import Optional

@dataclass
class ItemCreateDTO:
    """DTO для создания нового Item"""
    name: str
    quantity: int
    weight: float

@dataclass
class ItemDTO:
    """DTO для ответа API / представления Item"""
    item_id: UUID
    shipment_id: UUID
    name: str
    quantity: int
    weight: float

@dataclass
class ItemUpdateDTO:
    """
    DTO для обновления Item.
    Все поля Optional — подходит для PATCH (частичное обновление).
    Для PUT можно проверять, что все поля заполнены.
    """
    name: Optional[str] = None
    quantity: Optional[int] = None
    weight: Optional[float] = None
