"""
the utilities for zones
"""
from typing import Union, List

# from typing import List, Union, Any
# Zones information (number of wells)
# The zones should be all caps!
# ISYNTH (48): The reaction zones. Have extra functions that only works in these zones such as opening drawers.
# INJECT_I (2): only inject the liquid
# INJECT_L (2): injects the liquid, switch valve, and then triggers externally
# RACK_HS (0): zone for stirring heat-stir rack
# RACKL (80): 8mL vials rack next to ISYNTH
# RACKR (30): 20mL vials rack on the right side
# RACK4ML (24): 4mL vials on heat-stir rack in front position
# RACK4ML2 (24): 4mL vials on heat stir rack in back position
# SOLID (16): powder dispensing capsule locations
# SPE_C (80): solid phase extraction, collect position, inject solution from top and output to lower layer vials
# SPE_D (80): solid phase extraction, direct position, directly draw the solution from the lower layer vials
# SPE_W (80): solid phase extraction, collect position, inject solution from top and output to waste
# VALVEB (4): syringe pump valve position B, stock solutions
# WASTE (8): waste zone

# Helper and conversion methods
# Zones = Union[str, List]


class Zones(object):
    """
    holds and manages the zones for chemspeed
    every item in Zones is a valid zone in the chemspeed manager

    Attributes:
        valid_zones (dict): holds the valid zone names as keys to the number of wells in that zones
    """

    def __init__(self):
        """
        initializes Zones
        """
        self.valid_zones = {
            "ISYNTH": 48,
            "INJECT_I": 2,
            "INJECT_L": 2,
            "RACK_HS": 0,
            "RACKL": 80,
            "RACKR": 30,
            "RACK4ML": 24,
            "RACK4ML2": 24,
            "SOLID": 16,
            "SPE_C": 80,
            "SPE_D": 80,
            "SPE_W": 80,
            "VALVEB": 4,
            "WASTE": 8,
        }

    # def range_to_list(self, name: str, well_i: int = 1, well_f: int = 2):
    #     """A helper function to easily create a list of zones
    #
    #     Usage:
    #         zones('SOLID', 1, 2) == ['SOLID:1', 'SOLID:2']
    #
    #     Args:
    #         zone (str): Zone name
    #         well_i (int): first well
    #         well_f (int): last well
    #
    #     Returns:
    #         list: list of manager readable zones
    #     """
    #     assert name in self.valid_zones.keys(), f'{name} must be in {self.valid_zones.keys()}'
    #     assert well_i in range(1, self.valid_zones[name]) and well_f in range(1, self.valid_zones[name]) ,
    #
    #     return [f'{name}:{w}' for w in range(well_i, well_f + 1)]


def to_zone_string(zones: Union[Zones, str, List[str]]) -> str:
    """Return semicolon separated string of zones.

    Args:
        zones (Union[str, List]): List of zones, or string with zones separated
            by semicolons.

    Returns:
        str: Semicolon separated list of zones.
    """
    if isinstance(zones, list):
        return ";".join(zones)
    return str(zones)


def zones_list(zone: str, *wells):
    """A helper function to easily create a list of zones

    Usage:
        zones('SOLID', 1, 2) == ['SOLID:1', 'SOLID:2']

    Args:
        zone (str): Zone name
        *wells (list): list of well name (int or str)

    Returns:
        list: list of manager readable zones
    """
    return [zone + ":" + str(w) for w in wells]
