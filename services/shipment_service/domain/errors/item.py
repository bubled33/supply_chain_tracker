class ItemError(Exception):
    """Базовая ошибка для Item"""

class ItemQuantityError(ItemError):
    """Ошибка при некорректном значении количества"""

class ItemWeightError(ItemError):
    """Ошибка при некорректном значении веса"""

class ItemNotFoundError(ItemError):
    """Ошибка, если Item не найден в Shipment"""
