from dataclasses import dataclass

class FullNameError(ValueError):
    """Ошибка некорректного имени"""
    pass


@dataclass(frozen=True)
class FullName:
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise FullNameError("Name cannot be empty")

        if len(self.value.strip()) < 2:
            raise FullNameError(f"Name must be at least 2 chars long, got '{self.value}'")
