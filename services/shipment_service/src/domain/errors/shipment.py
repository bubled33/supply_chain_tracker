class ShipmentError(Exception):
    """Базовая ошибка для Shipment"""

class ShipmentStatusTransitionError(ShipmentError):
    """Ошибка при попытке некорректного перехода статуса"""

class ShipmentItemError(ShipmentError):
    """Ошибка при добавлении или удалении Item"""

class ShipmentNotFoundError(ShipmentError):
    """Ошибка, если Shipment не найден"""
