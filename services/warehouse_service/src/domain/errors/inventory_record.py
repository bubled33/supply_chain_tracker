class InventoryError(Exception):
    pass


class InventoryRecordNotFoundError(InventoryError):
    pass


class InventoryRecordAlreadyExistsError(InventoryError):
    pass


class InvalidInventoryStatusTransitionError(InventoryError):
    pass
