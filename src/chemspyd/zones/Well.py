from typing import Union

from .ChemspeedElement import ChemspeedElement
from ..exceptions import *


class Well(object):
    """
    Class for describing a single well on the ChemSpeed rack.
    """
    def __init__(
            self,
            element: ChemspeedElement,
            index: int,
            track_quantities: bool = False,
            logger: Optional[Logger] = None):
        """
        Instantiates the Well object by setting the

        Args:
            element: ChemspeedElement object that the specific well belongs to.
            index: Index / number of the well within the Manager zone.
            track_quantities: Whether to perform quantity tracking for this well.
        """
        self.element: ChemspeedElement = element
        self.index: int = index
        self._track_quantities: bool = False if track_quantities is False or element.default_quantity is None else True
        self._quantity: Optional[float] = element.default_quantity if self._track_quantities else None
        self.clean: bool = True if self._quantity == 0 else False
        self._state: str = "default"
        self._logger = logger

    @property
    def state(self) -> str:
        return self._state

    @state.setter
    def state(
            self,
            state="default"
    ) -> None:
        """
        Sets the well state (private self._state attribute) to the passed state.

        Args:
            state: Target state

        Raises:
            ChemspeedConfigurationError: if the target state is not possible for wells of the given element.
        """
        if state not in self.element.states:
            raise ChemspydElementError(
                f"Setting {self} to {state} failed. The element {self.element} cannot be set to {state}.",
                logger=self._logger
            )
        self._state = state

    @property
    def quantity(self):
        return self._quantity

    @quantity.setter
    def quantity(
            self,
            quantity: float
    ) -> None:
        """
        Sets the materials quantity value.

        Args:
            quantity: Quantity (mg for solids, mL for liquids) of material to be added to the well.
        """
        if quantity > 0:
            self.clean = False
        self._quantity = quantity

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

    def add_liquid(
            self,
            quantity: float
    ) -> None:
        """
        Updates the current material quantity in the vial by adding quantity to self._quantity.

        Args:
            quantity: Quantity (mL) of material to be added to the well.

        Raises:
            ChemspydElementError: if the well does not allow for adding liquid
            ChemspydQuantityError: if the well content would exceed the max. content or would be be lower than 0
        """
        if quantity >= 0 and not self.element.addable_liquid:
            raise ChemspydElementError(
                f"Dispense to {self} failed. Addition of liquid to element {self.element} is not allowed.",
                logger=self._logger
            )

        if self._track_quantities and self.element.max_volume:
            if self._quantity + quantity > self.element.max_volume:
                raise ChemspydQuantityError(
                    f"Dispense to {self} failed. The maximum volume will be exceeded.",
                    logger=self._logger
                )

            elif self._quantity + quantity < 0:
                raise ChemspydQuantityError(
                    f"Dispense from {self} failed. The well will be empty.",
                    logger=self._logger
                )

            self.quantity = self.quantity + quantity

    def remove_liquid(
            self,
            quantity: float
    ) -> None:
        """
        More intuitive-to-use method for removing material from the well.
        Calls the add_material() method with a negative quantity.

        Args:
            quantity: Quantity of material (mg for solids, mL for liquids) to be removed.

        Raises:
            ChemspydElementError: if the well does not allow for removing liquid
        """
        if not self.element.removable_liquid:
            raise ChemspydElementError(
                f"Dispense from {self} failed. Removing of liquid from element {self.element} is not allowed.",
                logger=self._logger
            )

        return self.add_liquid(-quantity)

    def add_solid(
            self,
            quantity: float
    ):
        """
        Checks if solid can be added to a given well.

        Args:
            quantity: Quantity (mg) of solid material to be added to the well.

        Raises:
            ChemspydElementError: if addition to well is not allowed.
        """
        if quantity >= 0 and not self.element.addable_solid:
            raise ChemspydElementError(
                f"Dispense to {self} failed. Addition of solid to element {self.element} is not allowed.",
                logger=self._logger
            )

    def remove_solid(
            self,
            quantity: float
    ):
        """
        Updates the current solid material quantity in the well by subtracting the quantity from self._quantity.

        Args:
            quantity: Quantity (mg) of material to be removed from the well.

        Raises:
            ChemspydElementError: if solid cannot be dispensed from the given well
            ChemspydQuantityError: if the dispense quantity exceeds the well content.
        """
        if not self.element.removable_solid:
            raise ChemspydElementError(
                f"Dispense from {self} failed. Removing of solid from element {self.element} is not allowed.",
                logger=self._logger
            )

        if self._track_quantities:
            if self._quantity - quantity < 0:
                raise ChemspydQuantityError(
                    f"Dispense from {self} failed. The well will be empty.",
                    logger=self._logger
                )

            self.quantity = self.quantity - quantity

    def validate_parameter(
            self,
            parameter_name: str,
            parameter_value: Union[int, float, str, bool]
    ) -> None:
        """
        Validates if a certain parameter can be set for the specific well.
        Wraps the validate_parameter() method of the ChemspeedElement class.

        Args:
            parameter_name: Key of the parameter (must be in self._required_keys).
            parameter_value: Value of the parameter.

        Raises:
            ChemspeedValueError: If the parameter value is not within the specified boundaries.
            ChemspeedConfigurationError: If the parameter cannot be set for the given element.
        """
        self.element.validate_parameter(parameter_name, parameter_value)

    def get_element_string(
            self
    ) -> str:
        """
        Returns the name of the element that the well belongs to.

        Returns:
            str: Element name
        """
        return self.element.states[self._state]
