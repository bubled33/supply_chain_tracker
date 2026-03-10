class WarehouseError(Exception):
    pass


class WarehouseNotFoundError(WarehouseError):
    pass


class WarehouseAlreadyExistsError(WarehouseError):
    pass


class WarehouseLocationUpdateError(WarehouseError):
    pass
