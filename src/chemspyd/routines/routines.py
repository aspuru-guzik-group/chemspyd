from typing import List, Union

from chemspyd import ChemspeedController
from chemspyd.exceptions.zone_exceptions import InvalidZoneError
from chemspyd.utils.zones import get_return_dst, to_zone_string


def prime_pumps(mgr: ChemspeedController, pump: int, volume: Union[int, float]) -> None:
    """
    primes chemspeed pumps

    Parameters
    ----------
    mgr: Chemspeed controller object
    pump: pump being primed
    volume: volume with which to prime pumps

    Returns
    -------
    None

    """
    if pump not in range(1, 5):
        raise InvalidZoneError(f"Pump {pump} is not a valid zone.")

    src = f'VALVEB:{pump}'
    dst = get_return_dst(src)

    mgr.transfer_liquid(
        source=src,
        destination=dst,
        volume=volume,
        src_flow=20,
        dst_flow=40,
        rinse_volume=0)
    print('Pumps primed.')


def inject_to_hplc(mgr: ChemspeedController,
                   source: Union[str, List[str]],
                   destination: Union[str, List[str]],
                   volume: float,
                   src_flow: float = 10,
                   src_bu: float = 3,
                   dst_flow: float = 0.5,
                   dst_bu: float = 0,
                   rinse_volume: float = 2,
                   ) -> None:
    """Inject liquid to the injection ports. This will use volume+0.1ml of liquid.

     Args (float for non specified type):
        source (str, list): zone for transfer source
        destination (str, list): zone for injection, can only be INJECT_I or INJECT_L
        volume: volume to transfer (mL)
        src_flow: draw speed at source (mL/min)
        src_bu: needle bottoms up distance at source (mm)
        dst_flow: draw speed at destination (mL/min)
        dst_bu: needle bottoms up distance at destination (mm)
        rinse_volume: needle rinsing volume after action (mL)
        """
    source = to_zone_string(source)
    # check if there
    destination = to_zone_string(destination)

    # TODO: Review that there are no important changes between inject_liquid() and transfer_liquid()!
    mgr.transfer_liquid(
        source=source,
        destination=destination,
        volume=volume,
        src_flow=src_flow,
        src_bu=src_bu,
        dst_flow=dst_flow,
        dst=dst_bu,
        bu=True,
        rinse_volume=rinse_volume
    )
