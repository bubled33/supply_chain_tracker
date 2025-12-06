from dataclasses import dataclass
from uuid import UUID
from typing import Optional

@dataclass
class CourierCreateDTO:
    """DTO для создания нового курьера"""
    name: str
    contact_info: str

@dataclass
class CourierDTO:
    """DTO для ответа API / представления курьера"""
    courier_id: UUID
    name: str
    contact_info: str

@dataclass
class CourierUpdateDTO:
    """
    DTO для обновления данных курьера.
    Поля Optional позволяют использовать этот DTO для PATCH-запросов
    (частичное обновление).
    """
    name: Optional[str] = None
    contact_info: Optional[str] = None
