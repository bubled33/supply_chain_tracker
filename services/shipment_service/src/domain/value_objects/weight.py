from dataclasses import dataclass

from src.domain.errors import WeightError


@dataclass(frozen=True)
class Weight:
    value: float

    def __post_init__(self):
        if self.value < 0:
            raise WeightError("Weight cannot be negative.")
