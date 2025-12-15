class WarehouseError(Exception):
    """Базовое исключение для домена Warehouse."""
    pass


class WarehouseNotFoundError(WarehouseError):
    """Склад не найден."""
    pass


class WarehouseAlreadyExistsError(WarehouseError):
    """Склад с такими данными уже существует."""
    pass


class WarehouseLocationUpdateError(WarehouseError):
    """Ошибка при обновлении локации склада."""
    pass
