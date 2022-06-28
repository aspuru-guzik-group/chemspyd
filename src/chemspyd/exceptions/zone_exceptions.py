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
