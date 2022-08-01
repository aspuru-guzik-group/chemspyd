class ZoneError(Exception):
    """
    Error to be raised when an action cannot be performed with a particular zone.
    """
    def __init__(self, *args):
        super().__init__(*args)


class InvalidZoneError(Exception):
    """
    Error to be raised when an invalid zone is specified.
    """
    def __init__(self, *args):
        super().__init__(*args)


class ChemspeedConfigurationError(Exception):
    """
    Exception to be raised when the hardware configuration does not allow for the targeted operation.
    """
    def __init__(self, *args):
        super().__init__(*args)


class ChemspeedValueError(Exception):
    """
    Exception to be raised when a specific value (e.g. of a parameter) is unfeasible.
    """
    def __init__(self, *args):
        super().__init__(*args)
