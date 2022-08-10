from typing import Union, List, Optional
from logging import Logger

from .Well import Well
from ..exceptions import *


class WellGroup(object):
    """
    Class describing a group of wells.
    Temporary object that is used internally to handle transfers from/to multiple wells at the same time.
    """
    def __init__(
            self,
            wells: Union[str, Well, List[str], List[Well]],
            well_configuration: dict,
            state: Optional[str] = None,
            logger: Optional[Logger] = None
    ):
        """
        Instantiates a WellGroup from
            - a single well name (str)
            - a single Well object
            - a list of well names (List[str])
            - a list of Well objects

        Converts all of these inputs to a list of Well objects, saved as self._all_wells.

        Args:
            wells: Single well (as str or Well object) or list of multiple wells (as str or Well object)
            well_configuration: Mapping of well names to Well objects.
            state (optional): Target state of the Well objects
            logger (optional): logger object
        """
        self._all_wells: List[Well] = self._get_well_list(wells, well_configuration)

        if state:
            self.set_state(state)

        self.logger: Logger = logger

    def _get_well_list(
            self,
            wells: Union[str, Well, List[str], List[Well]],
            well_configuration: dict
    ) -> List[Well]:
        """
        Static method to initialize a WellGroup by converting the different possible input formats (str, Well,
        List[str], List[Well]) into a list of Well objects.

        Args:
            wells: Single well (as str or Well object) or list of multiple wells (as str or Well object)
            well_configuration: Mapping of well names to Well objects.

        Returns:
            List[Well]: List of well objects.
        """
        if isinstance(wells, (str, Well)):
            wells = [wells]

        all_wells: list = []

        for well in wells:
            if isinstance(well, Well):
                all_wells.append(well)
            else:
                try:
                    all_wells.append(well_configuration[well][0](well_configuration[well][1]))
                except KeyError:
                    raise ChemspydZoneError(
                        f"Accessing the well object {well} failed. Key not found in the well configuration dictionary.",
                        logger=self.logger
                    )

        return all_wells

    @property
    def well_list(self):
        return self._all_wells

    def set_state(
            self,
            state: str
    ) -> None:
        """
        Sets the state of all wells in self._all_wells to the target state.

        Args:
            state: Name of the target state.
        """
        self._all_wells = [well(state) for well in self._all_wells]

    def set_parameter(
            self,
            parameter_name: str,
            parameter_value: Union[int, float, str, bool]
    ) -> None:
        """
        Public method to be called when each well of the WellGroup should be set to a certain value.
        For each well, validates if the parameter can be set for the specific well.

        Args:
            parameter_name: Name (attribute name / key) of the parameter.
            parameter_value: Target value of the parameter.
        """
        for well in self._all_wells:
            well.validate_parameter(parameter_name, parameter_value)

    def add_liquid(
            self,
            quantity: float
    ) -> None:
        """
        Public method to be called when adding liquid material to each well of the WellGroup.
        Validates the operation (viable addable quantity) and updates the material quantity of the well.

        Args:
            quantity: Quantity to be added to the well (in mL).
        """
        for well in self._all_wells:
            well.add_liquid(quantity)

    def remove_liquid(
            self,
            quantity: float
    ) -> None:
        """
        Public method to be called when removing liquid material from each well of the WellGroup.
        Validates the operation (viable removable quantity) and updates the material quantity of the well.

        Args:
            quantity: Quantity to be added to the well (in mL).
        """
        for well in self._all_wells:
            well.remove_liquid(quantity)

    def add_solid(
            self,
            quantity: float
    ) -> None:
        """
        Public method to be called when adding solid material to each well of the WellGroup.
        Validates the operation (viable addable quantity) and updates the material quantity of the well.

        Args:
            quantity: Quantity to be added to the well (in mg).
        """
        for well in self._all_wells:
            well.add_solid(quantity)

    def remove_solid(
            self,
            quantity: float
    ) -> None:
        """
        Public method to be called when removing solid material from each well of the WellGroup.
        Validates the operation (viable removable quantity) and updates the material quantity of the well.

        Args:
            quantity: Quantity to be added to the well (in mg).
        """
        for well in self._all_wells:
            well.remove_solid(quantity)

    def __str__(self) -> str:
        """
        Converts the list of wells into a single, semicolon-separated string of well names.

        Returns:
            str: Semicolon-separated list of wells that can be passed to the Manager.
        """
        return ";".join([str(well) for well in self._all_wells])

    def get_element_string(self) -> str:
        """
        Converts the element names of all wells into a single, semicolon-separated string.
        Removes duplicates by generating a set of element names.

        Returns:
             str: Semicolon-separated list of element names that can be passed to the manager.
        """
        element_strings: set = {well.get_element_string() for well in self._all_wells}
        return ";".join(element_strings)
