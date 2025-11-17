class ValueObjectError(Exception):
    """Базовая ошибка для всех Value Objects"""

class TimestampError(ValueObjectError):
    """Ошибка при создании некорректного Timestamp"""
