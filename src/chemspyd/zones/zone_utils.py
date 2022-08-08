from logging import Logger
from typing import Tuple, Optional

from .ChemspeedElement import ChemspeedElement
from .Well import Well


def initialize_zones(
        config: dict,
        track_quantities: bool = False,
        logger: Optional[Logger] = None
) -> Tuple[dict, dict]:
    """
    Initializes the hardware element objects and well objects from the corresponding configuration dictionary.
    Each dictionary entry must have the following format:
        $ELEMENT_NAME : {
            element_property_1: value1,
            element_property_2: value2,
            ...
        }

    Args:
        config: Configuration dictionary for all hardware elements.
        track_quantities: Whether to track compound quantities.
        logger (optional): Logger object

    Returns:
        elements: Dictionary of all element names (as keys) and pointers to the ChemspeedElement objects as values.
        wells: Dictionary[str, Tuple[Well, str]] of all well names (as keys) and (Well object, status) tuples as values.
    """
    elements: dict = dict()
    wells: dict = dict()

    for element_name in config:
        element: ChemspeedElement = ChemspeedElement(element_name, config[element_name], logger)
        elements[element_name] = element

        for well_idx in range(1, element.no_wells + 1):
            well: Well = Well(element, well_idx, track_quantities=track_quantities, logger=logger)

            # ATTN: The mapping of the different zone strings (e.g. SPE_D:1, SPE_W:1, SPE_C:1) to the same Well object
            #   with different states is required for now to allow for backward compatibility.
            #   Might be deprecated in future versions.
            for state in element.states:
                identifier = str(well(state))
                wells[identifier] = (well, state)

            well.state = "default"

    return elements, wells
