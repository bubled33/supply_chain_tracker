class CourierError(Exception):
    pass

class CourierNotFoundError(CourierError):
    pass

class CourierAlreadyExistsError(CourierError):
    pass

class CourierContactUpdateError(CourierError):
    pass
