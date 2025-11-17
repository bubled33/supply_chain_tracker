from dataclasses import dataclass

from services.shipment_service.domain.errors import LocationError


@dataclass(frozen=True)
class Location:
    country: str
    city: str
    address: str = ""

    def __post_init__(self):
        if not self.country or not self.city:
            raise LocationError("Country and city cannot be empty.")
