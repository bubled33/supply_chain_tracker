from dataclasses import dataclass



@dataclass(frozen=True)
class Location:
    country: str
    city: str
    address: str = ""

    def __post_init__(self):
        if not self.country or not self.city:
            raise ValueError("Country and city cannot be empty.")
