from typing import Union, List, Dict, Tuple
from chemspyd.exceptions import ChemspeedConfigurationError, ChemspeedValueError


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

# ATTN: Deprecated – will not be needed any more once the new Element / Well handling is operative
class Zones:
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


# ATTN: Might be deprecated soon, is also not used anywhere but in init_valid_zones()
def zones_list(zone: str, *wells: List[Union[int, str]]):
    """A helper function to easily create a list of zones

    Usage:
        zones('SOLID', 1, 2) == ['SOLID:1', 'SOLID:2']

    Args:
        zone (str): Zone name
        *wells (list): list of well name (int or str)

    Returns:
        list: list of manager readable zones
    """
    return [zone + ':' + str(w) for w in wells]

# ATTN: Contains a hard-coded mapping – should be somehow derived from file
def get_return_dst(dst: str) -> str:
    """
    Converts 'VALVEB' source to correct waste for system liquid dispensing.
    """
    valve2waste = {
        'VALVEB:1': 'WASTE1:1',
        'VALVEB:2': 'WASTE1:2',
        'VALVEB:3': 'WASTE1:3',
        'VALVEB:4': 'WASTE2:4'
    }
    return valve2waste[dst]


class ChemspeedElement(object):
    """
    Class for describing an element of the Chemspeed (e.g. ISynth, Filtration Rack, Vial Rack, ...) as a Python object.
    For consistent naming of wells, each element must be represented as a single zone in the Manager app.
    """

    _required_keys: set = {
        "no_wells",
        "max_quantity",
        "default_quantity",
        "has_heat",
        "has_stir",
        "has_reflux",
        "has_vacuum",
        "has_inert",
        "states"
    }

    def __init__(self, name: str, properties: dict) -> None:
        """
        Instantiates the ChemspeedElement object by setting all properties as attributes.

        Args:
            name: Name of the element (must match the zone name in the Manager app).
            properties: Dictionary of all specific properties of the element. Must contain the keys specified in the
                        class variable _required_keys.

        Raises:
            ChemspeedConfigurationError: if any of the required keys are missing.
        """
        self.name = name

        if not self._required_keys.issubset(properties):
            raise ChemspeedConfigurationError(
                f"Configuration of {name} failed. "
                f"Missing keys {self._required_keys - properties.keys()} for element {name}."
            )

        for key in properties:
            setattr(self, key, properties[key])

    def __str__(self) -> str:
        return self.name

    def validate_parameter(self, parameter_type: str, parameter: Union[int, float, bool]) -> None:
        """
        Validates a specific setting / target status (e.g. temperature, stir rate, ...) that the element should be
        set to.

        Args:
            parameter_type: Key of the parameter (must be in self._required_keys).
            parameter: Value of the parameter.

        Raises:
            ChemspeedValueError: If the parameter value is not within the specified boundaries.
            ChemspeedConfigurationError: If the parameter cannot be set for the given element.
        """
        try:
            lower_limit, upper_limit = getattr(self, parameter_type)

            if not lower_limit <= parameter <= upper_limit:
                raise ChemspeedValueError(
                    f"The set value of {parameter_type}:{parameter} exceeds the limit of {self.name}"
                )

        except (AttributeError, TypeError):
            raise ChemspeedConfigurationError(
                f"The parameter {parameter_type} cannot be set for {self.name}")


class Well(object):
    """
    Class for describing a single well on the ChemSpeed rack.
    """
    def __init__(self, element: ChemspeedElement, index: int, track_quantities: bool = False):
        """
        Instantiates the Well object by setting the

        Args:
            element: ChemspeedElement object that the specific well belongs to.
            index: Index / number of the well within the Manager zone.
            track_quantities: Whether to perform quantity tracking for this well.
        """
        self.element: ChemspeedElement = element
        self.index: int = index
        self._track_quantities = False if track_quantities is False or element.default_quantity is None else True
        self._quantity = element.default_quantity if self._track_quantities else None
        self._state = "default"

        # TODO: Include 'clean' property

    @property
    def state(self) -> str:
        return self._state

    @state.setter
    def state(self, state="default") -> None:
        """
        Sets the well state (private self._state attribute) to the passed state.

        Args:
            state: Target state

        Raises:
            ChemspeedConfigurationError: if the target state is not possible for wells of the given element.
        """
        if state not in self.element.states:
            raise ChemspeedConfigurationError(
                f"Setting {self} to {state} failed. The element {self.element} cannot be set to {state}."
            )
        self._state = state

    @property
    def quantity(self):
        return self._quantity

    @quantity.setter
    def quantity(self, quantity: float) -> None:
        """
        Sets the materials quantity value by calling the add_material method (allows for advanced exception handling).

        Args:
            quantity: Quantity (mg for solids, mL for liquids) of material to be added to the well.
        """
        self._quantity = 0
        self.add_material(quantity)

    def __str__(self) -> str:
        """
        Returns the zone identifier of the individual well from the element identifier and the index.

        Returns:
            str (element identifier and well index joined by ':')
        """
        return f"{self.element.states[self._state]}:{self.index}"

    def __call__(self, state: str = "default"):
        """
        Sets the state of the object to the passed state and returns a reference to the object itself.
        Allows for simultaneous state setting and generation of a pointer-type structure.

        Args:
            state:
        """
        self.state = state
        return self

    def add_material(self, quantity: float) -> None:
        """
        Updates the current material quantity in the vial by adding quantity to self._quantity.

        Args:
            quantity: Quantity (mg for solids, mL for liquids) of material to be added to the well.

        Raises:
            ChemspeedValueError: if vial is empty or maximum volume is exceeded
        """
        if self._track_quantities:
            if self._quantity + quantity > self.element.max_quantity:
                raise ChemspeedValueError(
                    f"Dispense to {self} failed. The maximum quantity will be exceeded."
                )

            elif self._quantity + quantity < 0:
                raise ChemspeedValueError(
                    f"Dispense to {self} failed. The well will be empty."
                )

            self._quantity += quantity

    def remove_material(self, quantity: float) -> None:
        """
        More intuitive-to-use method for removing material from the well.
        Calls the add_material() method with a negative quantity.

        Args:
            quantity: Quantity of material (mg for solids, mL for liquids) to be removed.
        """
        return self.add_material(-quantity)


def initialize_zones(config: dict, track_quantities: bool = False) -> Tuple[dict, dict]:
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

    Returns:
        elements: Dictionary of all element names (as keys) and pointers to the ChemspeedElement objects as values.
        wells: Dictionary[str, Tuple[Well, str]] of all well names (as keys) and (Well object, status) tuples as values.
    """

    # TODO: Figure out where exactly this function is called and how the elements and wells are passed to the manager
    #       - Ideal scenario:   pass the config to the constructor and call in __init__ of controller
    #                           !!! however, breaks the API !!!
    #       - Workaround:       create elements and wells als global variables and hard-code their loading into
    #                           the import of chemspyd (How to specify config file paths then)?
    #       - Other Solutions?

    elements: dict = dict()
    wells: dict = dict()

    for element_name in config:
        element: ChemspeedElement = ChemspeedElement(element_name, config[element_name])
        elements[element_name] = element

        for well_idx in range(1, element.no_wells + 1):
            well: Well = Well(element, well_idx, track_quantities=track_quantities)

            # ATTN: The mapping of the different zone strings (e.g. SPE_D:1, SPE_W:1, SPE_C:1) to the same Well object
            #   with different states is required for now to allow for backward compatibility.
            #   Might be deprecated in future versions.
            for state in element.states:
                identifier = str(well(state))
                wells[identifier] = (well, state)

            well.state = "default"

    return elements, wells


def to_zone_string(wells: Union[Well, str, List[Well], List[str]]) -> str:
    """Return semicolon separated string of zones.

    Args:
        wells: Group of wells, described as
                - a single Well object
                - a single string (either a single well name or semicolon-separated well names)
                - a list of Well objects
                - a list of strings

    Returns:
        str: Semicolon-separated list of wells that can be passed to the Manager for read-in.
    """
    if isinstance(wells, list):
        return ";".join([str(well) for well in wells])

    return str(wells)
