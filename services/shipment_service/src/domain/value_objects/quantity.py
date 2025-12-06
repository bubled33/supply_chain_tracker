from dataclasses import dataclass

from src.domain.errors import QuantityError


@dataclass(frozen=True)
class Quantity:
    value: int

    def __post_init__(self):
        if self.value < 1:
            raise QuantityError(f"Quantity must be at least 1, got {self.value}")
