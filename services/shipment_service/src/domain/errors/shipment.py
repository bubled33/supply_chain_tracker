class ShipmentError(Exception):

    pass
class ShipmentStatusTransitionError(ShipmentError):

    pass
class ShipmentItemError(ShipmentError):

    pass
class ShipmentNotFoundError(ShipmentError):
    pass
