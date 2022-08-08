from typing import Union, Optional
from logging import Logger

from ..exceptions import *


class ChemspeedElement(object):
    """
    Class for describing an element of the Chemspeed (e.g. ISynth, Filtration Rack, Vial Rack, ...) as a Python object.
    For consistent naming of wells, each element must be represented as a single zone in the Manager app.
    """

    _required_keys: set = {
        "no_wells",
        "max_quantity",
        "default_quantity",
        "addable",
        "removable",
        "thermostat",
        "stir",
        "reflux",
        "vacuum_pump",
        "drawer",
        "environment",
        "states"
    }

    def __init__(
            self,
            name: str,
            properties: dict,
            logger: Optional[Logger] = None
    ) -> None:
        """
        Instantiates the ChemspeedElement object by setting all properties as attributes.

        Args:
            name: Name of the element (must match the zone name in the Manager app).
            properties: Dictionary of all specific properties of the element. Must contain the keys specified in the
                        class variable _required_keys.
            logger (optional): Logger object

        Raises:
            ChemspeedConfigurationError: if any of the required keys are missing.
        """
        self.name = name
        self.logger = logger

        if not self._required_keys.issubset(properties):
            raise ChemspydPropertyError(
                f"Configuration of {name} failed. "
                f"Missing keys {self._required_keys - properties.keys()} for element {name}.",
                logger=self.logger
            )

        for key in properties:
            setattr(self, key, properties[key])

    def __str__(self) -> str:
        return self.name

    def validate_parameter(
            self,
            parameter_name: str,
            parameter_value: Union[int, float, str, bool]
    ) -> None:
        """
        Validates a specific setting / target status (e.g. temperature, stir rate, ...) that the element should be
        set to.

        Args:
            parameter_name: Key of the parameter (must be in self._required_keys).
            parameter_value: Value of the parameter.

        Raises:
            ChemspeedValueError: If the parameter value is not within the specified boundaries.
            ChemspeedConfigurationError: If the parameter cannot be set for the given element.
        """
        validation_methods: dict = {
            str: self._validate_discrete_parameter,
            bool: self._validate_discrete_parameter,
            int: self._validate_continuous_parameter,
            float: self._validate_continuous_parameter
        }

        try:
            validation_methods[type(parameter_value)](parameter_name, parameter_value)

        except (KeyError, AttributeError, TypeError):
            raise ChemspydElementError(
                f"The parameter {parameter_name} cannot be set for {self.name}",
                logger=self.logger
            )

    def _validate_continuous_parameter(
            self,
            parameter_name: str,
            parameter_value: Union[int, float]
    ) -> None:
        """
        Validates if a continuous parameter is in the specified boundaries,
        given as [lower, upper] in the configuration.

        Args:
            parameter_name: Key of the parameter
            parameter_value: Value of the parameter.
        """
        boundaries: list = getattr(self, parameter_name)

        if not boundaries[0] <= parameter_value <= boundaries[1]:
            raise ChemspydRangeError(
                f"The set value of {parameter_name} ({parameter_value}) exceeds the limit of {self.name}.",
                logger=self.logger
            )

    def _validate_discrete_parameter(
            self,
            parameter_name: str,
            parameter_value: Union[str, bool]
    ) -> None:
        """
        Validates if a discrete parameter is in the specified set of options.

        Args:
            parameter_name: Key of the parameter
            parameter_value: Value of the parameter.
        """
        options: list = getattr(self, parameter_name)

        if parameter_value not in options:
            raise ChemspydRangeError(
                f"The set value of {parameter_name} ({parameter_value}) is not a feasible option for {self.name}.",
                logger=self.logger
            )
