from typing import Union, List

from .ChemspeedElement import ChemspeedElement
from .WellGroup import WellGroup
from .Well import Well
from .zone_utils import initialize_zones

# Definition of Zone type to unify string and well definition of zones (might be deprecated in the future)
Zone: type = Union[str, Well, List[str], List[Well]]
