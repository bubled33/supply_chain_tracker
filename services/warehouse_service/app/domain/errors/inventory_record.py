class InventoryError(Exception):
    """Базовое исключение для домена Inventory."""
    pass


class InventoryRecordNotFoundError(InventoryError):
    """Запись инвентаря не найдена."""
    pass


class InventoryRecordAlreadyExistsError(InventoryError):
    """Запись инвентаря уже существует."""
    pass


class InvalidInventoryStatusTransitionError(InventoryError):
    """Недопустимый переход статуса инвентаря."""
    pass
