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
