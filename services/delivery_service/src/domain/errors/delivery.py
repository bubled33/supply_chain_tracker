class DeliveryError(Exception):
    """Базовое исключение для домена Delivery"""
    pass

class DeliveryNotFoundError(DeliveryError):
    """Ошибка: доставка не найдена"""
    pass

class DeliveryStatusTransitionError(DeliveryError):
    """
    Ошибка: некорректный переход статуса.
    Например, попытка перейти из DELIVERED обратно в ASSIGNED.
    """
    pass

class DeliveryCourierAssignmentError(DeliveryError):
    """
    Ошибка при назначении курьера.
    Например, попытка назначить курьера, который уже занят другой доставкой
    (если бизнес-правила это запрещают).
    """
    pass

class DeliveryTimeError(DeliveryError):
    """
    Ошибка, связанная с временными метками.
    Например, попытка установить фактическое время доставки раньше времени создания.
    """
    pass
