from scipy.constants import *


class UnitConverter(object):

    def __init__(self):
        """
        Constructor for a unit converter, sets up a factory pattern for matching the variable types to convert with
        the corresponding converter methods.
        """
        self.converter_factory: dict = {
            "temperature": self._convert_temperature,
            "pressure": self._convert_pressure,
            "mass": self._convert_mass,
            "time": self._convert_time,
            "float": self._no_conversion,
        }

    def __call__(self, parameter_type: str, value: float, source_unit: str, target_unit: str, accuracy: int = 1) -> float:
        """
        Uses the converter factory pattern to call the converter function depending on the parameter type.

        Args:
            parameter_type: Name of the parameter type.
            value: Value of the parameter to convert.
            source_unit: Name of the source unit.
            target_unit: Name of the target unit.

        Returns:
            float: Converted value
        """
        return self.converter_factory[parameter_type](value, source_unit, target_unit)

    @staticmethod
    def _convert_temperature(value: float, source_unit: str, target_unit: str, accuracy: int = 1) -> float:
        """
        Converts temperatures using scipy's convert_temperature method.

        Args:
            value: Temperature value to convert
            source_unit: Name of the source unit (e.g. K, C, F)
            target_unit: Name of the target unit
            accuracy: Number of digits after the comma

        Returns:
            float: Converted temperature, rounded.
        """
        return round(convert_temperature(value, source_unit, target_unit), accuracy)

    @staticmethod
    def _convert_time(value: float, source_unit: str, target_unit: str, accuracy: int = 1) -> float:
        """
        Converts times using scipy's internal constants

        Args:
            value: Time value to convert
            source_unit: Name of the source unit (e.g. second, minute, hour, milli, micro, ...)
            target_unit: Name of the target unit
            accuracy: Number of digits after the comma

        Returns:
            float: Converted time, rounded.
        """
        if source_unit == "second":
            source_unit = "1"
        if target_unit == "second":
            target_unit = "1"

        return round(value * eval(source_unit) / eval(target_unit), accuracy)

    @staticmethod
    def _convert_mass(value: float, source_unit: str, target_unit: str, accuracy: int = 2) -> float:
        """
        Converts masses using scipy's internal constants

        Args:
            value: Time value to convert
            source_unit: Name of the source unit (e.g. milli, micro, kilo)
            target_unit: Name of the target unit
            accuracy: Number of digits after the comma.

        Returns:
            float: Converted mass, rounded
        """
        return round(value * eval(source_unit) / eval(target_unit), accuracy)

    @staticmethod
    def _convert_pressure(value: float, source_unit: str, target_unit: str, accuracy: int = 2) -> float:
        """
        Converts pressures using scipy's internal constants

        Args:
            value: Pressure value to convert
            source_unit: Name of the source unit (e.g. Pa, mbar, milli, micro, kilo)
            target_unit: Name of the target unit
            accuracy: Number of digits after the comma.

        Returns:
            float: Converted mass, rounded
        """
        if source_unit == "Pa":
            source_unit = "1"
        if target_unit == "Pa":
            target_unit = "1"

        if source_unit == "mbar":
            source_unit = milli * bar
        if target_unit == "mbar":
            target_unit = milli * bar

        return round(value * eval(source_unit) / eval(target_unit), accuracy)

    @staticmethod
    def _no_conversion(value: float, **kwargs) -> float:
        """
        Leave value unchanged. Here to allow convenient mapping of values to converter functions.

        Args:
            value: Value to return unchanged.
            kwargs: Unused, only for similar API across all converter functions.

        Returns:
            float: Unchanged value
        """
        return value