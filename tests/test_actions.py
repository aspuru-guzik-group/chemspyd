from chemspyd import ChemspeedController
from chemspyd.exceptions import ChemspeedConfigurationError


def test_invalid_liquid_transfer():

    controller = ChemspeedController(
        cmd_folder="",
        simulation=True
    )

    with pytest.raises(ChemspeedConfigurationError) as exc_info:

        controller.transfer_liquid(
            source="RACKR:1",
            destination="VALVEB:1",
            volume=1
        )

        assert str(exc_info.value) == "Dispense to VALVEB:1 failed. Addition of material to element VALVEB is not allowed."