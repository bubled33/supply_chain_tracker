class CourierError(Exception):
    """Базовое исключение для домена Courier"""
    pass

class CourierNotFoundError(CourierError):
    """Ошибка: курьер не найден"""
    pass

class CourierAlreadyExistsError(CourierError):
    """Ошибка: курьер с такими данными уже существует"""
    pass

class CourierContactUpdateError(CourierError):
    """Ошибка при попытке обновления контактных данных"""
    pass
