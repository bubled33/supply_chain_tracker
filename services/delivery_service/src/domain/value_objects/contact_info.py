from dataclasses import dataclass

class ContactInfoError(ValueError):
    """Ошибка некорректного формата контактных данных"""
    pass


@dataclass(frozen=True)
class ContactInfo:
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ContactInfoError("Contact info cannot be empty")

        if len(self.value.strip()) < 5:
            raise ContactInfoError(f"Contact info is too short, got '{self.value}'")
