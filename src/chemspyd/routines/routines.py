import time
from typing import Union

from chemspyd import Controller
from chemspyd.zones import Zone, WellGroup
from chemspyd.exceptions import ChemspydZoneError
from chemspyd.utils import UnitConverter

def prime_pumps(
        mgr: Controller,
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
    try:
        src = mgr.system_liquids[str(pump)]["liquid_zone"]
        dst = mgr.system_liquids[str(pump)]["waste_zone"]
    except KeyError:
        raise ChemspydZoneError("The specified zone does not exist.")

    mgr.transfer_liquid(
        source=src,
        destination=dst,
        volume=volume,
        src_flow=20,
        dst_flow=40,
        rinse_volume=0)


def inject_to_hplc(
        mgr: Controller,
        source: Zone,
        destination: Zone,
        volume: float,
        needle: int = 0,
        src_flow: float = 10,
        src_bu: bool = True,
        src_distance: float = 3,
        dst_flow: float = 0.5,
        rinse_volume: float = 2,
        rinse_after_valve_switch: bool = True
) -> None:
    """
    Inject liquid to the injection ports. This will use volume + 0.1ml of liquid.

    Args:
        mgr: Controller object
        source (Zone): Zone for transfer source
        destination (Zone): Injection zone
        volume: volume to transfer (mL)
        needle: Number of the needle to be used for injection.
        src_flow: draw speed at source (mL/min)
        src_bu: True if liquid should be drawn bottom-up at the source.
        src_distance: Needle bottom-up / top-down distance at source (mm)
        dst_flow: Dispense speed at destination (mL/min)
        rinse_volume: needle rinsing volume after action (mL)
        rinse_after_valve_switch: True if needle should only be rinsed after switching the HPLC valve.
    """
    source = WellGroup(source, well_configuration=mgr.wells)
    destination = WellGroup(destination, well_configuration=mgr.wells, state="load")

    if rinse_after_valve_switch:
        rinse_volume_init: float = 0
    else:
        rinse_volume_init: float = rinse_volume

    mgr.transfer_liquid(
        source=source.get_zone_string(),
        destination=destination.get_zone_string(),
        volume=volume,
        needle=needle,
        src_flow=src_flow,
        src_bu=src_bu,
        src_distance=src_distance,
        dst_flow=dst_flow,
        dst_bu=True,
        rinse_volume=rinse_volume_init
    )

    if rinse_after_valve_switch:
        mgr.transfer_liquid(
            source=mgr.system_liquids[str(needle)]["liquid_zone"],
            destination=mgr.system_liquids[str(needle)]["waste_zone"],
            volume=rinse_volume,
            rinse_volume=rinse_volume
        )


def do_schlenk_cycles(
        mgr: Controller,
        wells: Zone,
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
        time.sleep(0.5)  # ATTN: Implemented because of random communication delays. Test if it is necessary.
        mgr.set_vacuum(vac_zone=wells, state="on", vacuum=vacuum_pressure)
        mgr.wait(evac_time)

        # Backfilling
        mgr.set_drawer(zone=wells, state="close", environment="inert")
        time.sleep(0.5)  # ATTN: Implemented because of random communication delays. Test if it is necessary.
        mgr.set_vacuum(vac_zone=wells, state="on", vacuum=1000)
        mgr.wait(backfill_time)

    mgr.set_isynth_vacuum(state="off")
    mgr.set_drawer(zone=wells, state="close", environment="none")


def heat_under_reflux(
        mgr: Controller,
        wells: Zone,
        stir_rate: float,
        temperature: float,
        heating_hours: int,
        cooling_hours: int,
        condenser_temperature: float = 0,
        ramp: float = 0
) -> None:
    """
    Sets up the heating and the reflux condenser for a specified time period.
    Cools the system back to room temperature for a specified cooling period.

    ATTN: Might also influence neighboring vials (e.g. it can only heat the entire element).
          Maybe this should be taken into account somehow.

    Args:
        mgr: Controller object.
        wells: Wells to be heated under reflux.
        stir_rate: Stir rate (in rpm).
        temperature: Heating temperature (in °C)
        heating_hours: Heating time (in h).
        cooling_hours: Cooling time (in h).
        condenser_temperature: Temperature (in °C) of the reflux condenser.
        ramp: Ramping speed (in °C / min) for the cryostat.
    """
    mgr.set_reflux(wells, state="on", temperature=condenser_temperature)
    mgr.set_temperature(wells, state="on", temperature=temperature, ramp=ramp)
    mgr.set_stir(wells, state="on", rpm=stir_rate)
    mgr.wait(UnitConverter()("time", heating_hours, "hour", "second"))
    mgr.set_temperature(wells, state="on", temperature=20, ramp=ramp)
    mgr.wait(UnitConverter()("time", cooling_hours, "hour", "second"))
    mgr.set_temperature(wells, state="off")
    mgr.set_reflux(wells, state="off")
    mgr.set_stir(wells, state="off")


def filter_liquid(
        mgr: Controller,
        source_well: Zone,
        filtration_zone: Zone,
        filtration_volume: float,
        collect_filtrate: bool = True,
        wash_liquid: Zone = "",
        wash_volume: float = 0,
        collect_wash: bool = False,
        eluent: Zone = "",
        eluent_volume: float = 0
):
    """
    Filters a liquid sample on a filtration rack. Allows for collecting the filtrate, washing and eluting the filter.

    Args:
        mgr: Controller object.
        source_well: Source well of the sample to be filtered.
        filtration_zone: Zone on the filtration rack to be used. All "sub-zones" (SPE_D, SPE_C, SPE_W can be used).
        filtration_volume: Volume (in mL) of liquid to be filtered.
        collect_filtrate: Whether to collect or dispose the filtrate
        wash_liquid: Source zone of the wash liquid.
        wash_volume: Volume (in mL) of wash liquid.
        collect_wash: Whether to collect or dispose the wash liquid.
        eluent: Source zone of the eluent.
        eluent_volume: Volume of eluent to be used.
    """
    filtration_zone = WellGroup(filtration_zone, mgr.wells)
    filtrate_state: str = "collect" if collect_filtrate else "waste"
    wash_state: str = "collect" if collect_wash else "waste"

    # Transfer liquid to filtration zone and collect or dispose the filtrate
    filtration_zone.set_state(filtrate_state)
    mgr.transfer_liquid(
        source=source_well,
        destination=filtration_zone.well_list,
        volume=filtration_volume
    )

    # Wash the filter and collect or dispose the wash liquid
    if wash_volume > 0:
        filtration_zone.set_state(wash_state)
        mgr.transfer_liquid(
            source=wash_liquid,
            destination=filtration_zone.well_list,
            volume=wash_volume
        )

    # Elute from the filter and collect the eluent.
    if eluent_volume > 0:
        filtration_zone.set_state("collect")
        mgr.transfer_liquid(
            source=eluent,
            destination=filtration_zone.well_list,
            volume=eluent_volume
        )

