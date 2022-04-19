"""
this file contains the functionality necessary for converting between units for chemspeed use
"""
from typing import Any
# ATTN: Should we have an error for negative temp and pressure input values?
#  or even a warning for 0 pressure?


def temp_k_to_c(temp_kelvin: float) -> float:
    """Convert temperature in Kelvin to °C and round result to 5 decimal places.

    Args:
        temp_kelvin (float): Temperature in Kelvin.

    Returns:
        float: Temperature in °C rounded to 5 decimal places.
    """
    return round(temp_kelvin - 273.15, 5)


def pressure_pa_to_mbar(pressure_pa: float) -> float:
    """Convert pressure in Pa to mbar and round result to 5 decimal places.

    Args:
        pressure_pa (float): Pressure in Pa.

    Returns:
        float: Pressure in Pa rounded to 5 decimal places.
    """
    return round(pressure_pa / 100., 5)


def no_change(value: Any) -> Any:
    """Leave value unchanged. Here to allow convenient mapping of values to
    converter functions.

    Args:
        value (Any): Value to return unchanged.

    Returns:
        Any: value unchanged.
    """
    return value
