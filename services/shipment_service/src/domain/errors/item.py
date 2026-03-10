class ItemError(Exception):

    pass
class ItemQuantityError(ItemError):

    pass
class ItemWeightError(ItemError):

    pass
class ItemNotFoundError(ItemError):
    pass
