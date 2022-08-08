from typing import Optional
from logging import Logger


class ChemspydError(Exception):
    """
    Parent class for any exceptions raised by ChemsPyd.
    A logging.Logger object can be passed as an optional keyword argument to the constructor, and will then
    automatically log the error type and error message on the logger.ERROR level.
    """
    def __init__(self, *args, logger: Optional[Logger] = None):
        super().__init__(*args)
        if logger:
            logger.error(f"ERROR - {type(self).__name__}: {self}")


class ChemspydRangeError(ChemspydError):
    """
    Exception for values and parameters that are not in a specified range.
    """


class ChemspydQuantityError(ChemspydError):
    """
    Exception for well quantities that exceed the limits of well capacity.
    """


class ChemspydPropertyError(ChemspydError):
    """
    Exception for missing properties and attributes for specific elements of the Chemspeed hardware.
    """


class ChemspydElementError(ChemspydError):
    """
    Exception for invalid element configuration for performing a specific operation.
    """


class ChemspydZoneError(ChemspydError):
    """
    Exception regarding zone definitions, keys etc.
    """


class ChemspydCommunicationError(ChemspydError):
    """
    Exception regarding file communication with AutoSuite.
    """