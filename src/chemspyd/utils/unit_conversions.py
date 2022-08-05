from typing import Any, Union
from scipy.constants import *


def temp_k_to_c(temp_kelvin: float) -> float:
    """Convert temperature in Kelvin to °C and round result to 5 decimal places.

    Args:
        temp_kelvin (float): Temperature in Kelvin.

    Returns:
        float: Temperature in °C rounded to 5 decimal places.
    """
    return convert_temperature(temp_kelvin, "K", "C")


def hours_to_seconds(time_hours: float) -> Union[int, float]:
    """
    Converts the time in hours to seconds and rounds the result to 0 decimal places.

    Args:
        time_hours: Time in hours.

    Returns:
        float: time in seconds
    """
    return round(time_hours * hour)


def pressure_pa_to_mbar(pressure_pa: float) -> float:
    """Convert pressure in Pa to mbar and round result to 5 decimal places.

    Args:
        pressure_pa (float): Pressure in Pa.

    Returns:
        float: Pressure in Pa rounded to 5 decimal places.
    """
    return round(pressure_pa / 100., 5)


def convert_mass(mass: float, original: str = "kilo", dst: str = "milli") -> float:
    """
    Converts a mass from one mass unit to another.

    Args:
        mass: Value of the mass
        original: Prefix of the mass passed (default: "kilo" -> kg)
        dst: Desired prefix of the mass (default: "milli" -> mg)
    """
    mass_converted: float = mass * eval(original) / eval(dst)
    return round(mass_converted, 1)


def no_change(value: Any) -> Any:
    """Leave value unchanged. Here to allow convenient mapping of values to
    converter functions.

    Args:
        value (Any): Value to return unchanged.

    Returns:
        Any: value unchanged.
    """
    return value
