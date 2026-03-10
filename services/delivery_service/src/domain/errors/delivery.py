class DeliveryError(Exception):
    pass

class DeliveryNotFoundError(DeliveryError):
    pass

class DeliveryStatusTransitionError(DeliveryError):
    pass

class DeliveryCourierAssignmentError(DeliveryError):
    pass

class DeliveryTimeError(DeliveryError):
    pass
