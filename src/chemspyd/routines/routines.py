import time
from typing import List, Union

from chemspyd import ChemspeedController
from chemspyd.exceptions.zone_exceptions import InvalidZoneError
from chemspyd.utils.zones import get_return_dst, to_zone_string
from chemspyd.utils.unit_conversions import hours_to_seconds


def prime_pumps(
        mgr: ChemspeedController,
        pump: int,
        volume: Union[int, float]
) -> None:
    """
    Primes the ChemSpeed pumps.

    Args:
        mgr: Chemspeed controller object
        pump: pump being primed
        volume: volume with which to prime pumps

    Returns:
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


def do_schlenk_cycles(
        mgr: ChemspeedController,
        wells: Union[str, List[str]],
        evac_time: int = 60,
        backfill_time: int = 30,
        vacuum_pressure: float = 1,
        no_cycles: int = 3
) -> None:
    """
    Performs Schlenk Cycles (evacuate-refill cycles) on the specified wells.
    Requires the wells to be in an element that supports vacuum/inert gas handling.
    ATTN: Might also influence neighboring wells (e.g. if they are in the same ISYNTH drawer).

    Args:
        mgr: Chemspeed controller object
        wells: Zones to be set to inert gas.
        evac_time: Time (in sec) for evacuation. Default: 60 sec.
        backfill_time: Time (in sec) for backfilling with inert gas. Default: 30 sec.
        vacuum_pressure: Pressure (in mbar) that should be targeted for evacuation. Default: 1 mbar (minimum).
        no_cycles: Number of Schlenk cycles. Default: 3.
    """
    for _ in range(no_cycles):
        # Evacuation
        mgr.set_drawer(zone=wells, state="close", environment="vacuum")
        time.sleep(0.5)  # TODO: Implemented because of random communication delays. Test if it is necessary.
        mgr.set_isynth_vacuum(state="on", vacuum=vacuum_pressure)
        mgr.wait(evac_time)

        # Backfilling
        mgr.set_drawer(zone=wells, state="close", environment="inert")
        time.sleep(0.5)  # TODO: Implemented because of random communication delays. Test if it is necessary.
        mgr.set_isynth_vacuum(state="on", vacuum=1000)
        mgr.wait(backfill_time)

    mgr.set_isynth_vacuum(state="off")
    mgr.set_drawer(zone=wells, state="close", environment="none")


def heat_under_reflux(
        mgr: ChemspeedController,
        wells: Union[str, List[str]],
        temperature: float,
        heating_hours: int,
        cooling_hours: int,
        condenser_temperature: float = 0,
        ramp: float = 0
) -> None:
    """
    Sets up the heating and the reflux condenser for a specified time period.
    Cools the system back to room temperature for a specified cooling period.
    ATTN: Might also influence neighboring vials (e.g. it can only heat the

    Args:
        mgr: ChemspeedController object.
        wells: Wells to be heated under reflux.
        temperature: Heating temperature (in °C)
        heating_hours: Heating time (in h).
        cooling_hours: Cooling time (in h).
        condenser_temperature: Temperature (in °C) of the reflux condenser.
        ramp: Ramping speed (in °C / min) for the cryostat.
    """
    mgr.set_reflux(wells, state="on", temperature=condenser_temperature)
    mgr.set_temperature(wells, state="on", temperature=temperature, ramp=ramp)
    mgr.wait(hours_to_seconds(heating_hours))
    mgr.set_temperature(wells, state="on", temperature=20, ramp=ramp)
    mgr.wait(cooling_hours)
    mgr.set_temperature(wells, state="off")
    mgr.set_reflux(wells, state="off")


def filter_liquid(
        mgr: ChemspeedController,
        source_well: Union[str, List[str]],
        filtration_zone: Union[str, List[str]],
        filtration_volume: float,
        collect_filtrate: bool = True,
        wash: bool = False,
        wash_liquid: Union[str, List[str]] = "",
        wash_volume: float = 0,
        collect_wash: bool = False,
        elution: bool = False,
        eluent: Union[str, List[str]] = "",
        eluent_volume: float = 0
):
    """
    Filters a liquid sample through a filter.

    Args:
        mgr: ChemspeedController object.
        source_well: Source well of the sample to be filtered.
        filtration_zone: Zone on the filtration rack to be used   ATTN: What exactly is this?
        filtration_volume: Volume (in mL) of liquid to be filtered.
        collect_filtrate: Whether to collect or dispose the filtrate
        wash: Whether to wash the solid residue.
        wash_liquid: Source zone of the wash liquid.
        wash_volume: Volume (in mL) of wash liquid.
        collect_wash: Whether to collect or dispose the wash liquid.
        elution: Whether to do an additional elution step.
        eluent: Source zone of the eluent.
        eluent_volume: Volume of eluent to be used.

    TODO: How should this specifically be set up?
        - What is the source / target zone? A specific collection / drawing / waste zone? Or just the "Number" on the SPE rack? Requires Well / Zone objects?
        - Which options should be provided? Wash? Elute?

    TODO: Discuss if bool arguments (wash, elution) are necessary or can be identical to volume > 0
    """
    # raise NotImplementedError

    collect_zone, waste_zone = get_filtration_zones(filtration_zone)  # TODO: implement this method?

    filtrate_zone: str = collect_zone if collect_filtrate else waste_zone

    mgr.transfer_liquid(
        source=source_well,
        destination=filtrate_zone,
        volume=filtration_volume
    )

    if wash:
        wash_zone: str = collect_zone if collect_wash else waste_zone
        mgr.transfer_liquid(
            source=wash_liquid,
            destination=wash_zone,
            volume=wash_volume
        )

    if elution:
        mgr.transfer_liquid(
            source=eluent,
            destination=collect_zone,
            volume=eluent_volume
        )

