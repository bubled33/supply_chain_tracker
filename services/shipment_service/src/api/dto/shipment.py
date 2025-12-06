from dataclasses import dataclass
from datetime import date
from typing import Optional
from uuid import UUID

@dataclass
class LocationDTO:
    """DTO для Location VO"""
    country: str
    city: str
    address: str = ""

@dataclass
class ShipmentCreateDTO:
    origin: LocationDTO
    destination: LocationDTO
    departure_date: date

@dataclass
class ShipmentUpdateDTO:
    origin: Optional[LocationDTO] = None
    destination: Optional[LocationDTO] = None
    departure_date: Optional[date] = None
    arrival_date: Optional[date] = None
    status: Optional[str] = None

@dataclass
class ShipmentDTO:
    shipment_id: UUID
    origin: LocationDTO
    destination: LocationDTO
    departure_date: date
    arrival_date: Optional[date]
    status: str
    created_at: str
    updated_at: str
