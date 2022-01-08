'''
This file contains the functionality for the checking of user inputs into the chemspeed controller.

'''
from typing import List, Union, Any
import os
import time
from utils.zones import Zones, zones_list


def init_valid_zones() -> List[str]:
    """
    Return a list of all valid zones

    Returns:
        List of valid zones
    """
    valid_zones = ['RACK_HS']
    z = {
        'ISYNTH': 48,
        'INJECT_I': 2,
        'INJECT_L': 2,
        'RACK_HS': 0,
        'RACKL': 80,
        'RACKR': 30,
        'RACK4ML': 24,
        'RACK4ML2': 24,
        'SOLID': 16,
        'SPE_C': 80,
        'SPE_D': 80,
        'SPE_W': 80,
        'VALVEB': 4,
        'WASTE': 8
    }
    for key in z:
        valid_zones.extend(zones_list(key, z[key]))

    return valid_zones


def validate_zones(valid_zones: Zones, zones: Zones) -> bool:
    """
    checks that all zones are valid

    :param valid_zones: list of valid zones
    :param zones: zones being checked
    :return: true if all zones are valid
    """
    if isinstance(zones, int):
        if zones in valid_zones:
            return True
        else:
            return False
    elif isinstance(zones, List):
        for zone in zones:
            if zone not in valid_zones:
                return False
        return True
    else:
        return False
