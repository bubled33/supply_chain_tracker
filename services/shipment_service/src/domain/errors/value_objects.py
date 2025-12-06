from libs.errors.value_objects import ValueObjectError


class QuantityError(ValueObjectError):
    """Ошибка валидации количества"""

class WeightError(ValueObjectError):
    """Ошибка валидации веса"""

class LocationError(ValueObjectError):
    """Ошибка при создании некорректного Location"""
