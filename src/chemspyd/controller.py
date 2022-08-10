#!/usr/bin/python
# -*- coding: UTF-8 -*-

from typing import Dict, List, Union, Optional
from pathlib import Path
from logging import Logger
from deprecation import deprecated

from .executor import ChemspeedExecutor
from chemspyd.utils.logging_utils import get_logger
from chemspyd.utils import UnitConverter
from chemspyd.utils import load_json
from chemspyd.zones import Zone, WellGroup, initialize_zones


class Controller(object):
    """
    Central Controller class for Python control of a ChemSpeed robotic platform.
    High-level, public interface ChemsPyd package.
    """

    # ATTN: API Broken compared to ChemsPyd 0.2!
    def __init__(
            self,
            cmd_folder: Union[str, Path],
            element_config: Union[str, Path],
            system_liquids: Union[str, Path],
            status_keys: Union[str, Path],
            stdout: bool = True,
            logfile: Optional[Union[str, Path]] = None,
            verbosity: int = 3,
            simulation: bool = False,
            track_quantities: bool = False
    ) -> None:
        """
        Initializes the Controller by:
            - instantiating the ChemspeedExecutor object, handling the communication with the AutoSuiteExecutor
            - establishing logging
            - loading the instrument configuration

        Args:
            cmd_folder: Path to the folder containing the csv files for communicating with the instrument.
            element_config: Path to the .json file containing the configuration of the ChemspeedElements.
            system_liquids: Path to the .json file containing the configuration of the pumps and system liquids.
            status_keys: Path to the .json file containing the configuration of the status file.
            stdout: True if logging output should be displayed on the console.
            logfile: Path to the log file. If None, no log file is written.
            simulation: True in order to run the Python controller (not Autosuite!) in simulation mode.
                        Will only print execution statements then (without sending any commands to the instrument).
            track_quantities: True if vial volumes should be rigorously tracked.

        """
        self.logger: Logger = get_logger(stdout, logfile)

        self.chemspeed: ChemspeedExecutor = ChemspeedExecutor(cmd_folder, self.logger, verbosity, simulation)

        self.system_liquids: dict = load_json(system_liquids)
        self.elements, self.wells = initialize_zones(load_json(element_config), track_quantities, self.logger)
        self.status_keys: dict = load_json(status_keys)

    ##################################
    # High Level Chemspeed Functions #
    ##################################

    # ATTN: API Broken compared to ChemsPyd 0.2!
    def transfer_liquid(
            self,
            source: Zone,
            destination: Zone,
            volume: float,
            needle: int = 0,
            src_flow: float = 10,
            src_bu: bool = True,
            src_distance: float = 3,
            dst_flow: float = 10,
            dst_bu: bool = False,
            dst_distance: float = 5,
            rinse_volume: float = 2,
            rinse_stn: int = 1,
            airgap: float = 0.01,
            post_airgap: float = 0,
            airgap_dst: Zone = 'WASTE',
            extra_volume: float = 0,
            extra_dst: Zone = 'WASTE',
            equib_src: float = 0,
            equib_dst: float = 0,
            multiple_asp: bool = False,
    ):
        """
        Executes a liquid transfer on the Chemspeed platform.

        Args:
            source: Source zone for the liquid transfer.
            destination: Destination zone for the liquid transfer.
            volume: volume to transfer (0 mL <= volume <= 20 mL)
            needle: Number of the needle to use (0 means all needles).
            src_flow: draw speed at source (0.05 mL/min <= src_flow <= 125 mL/min)
            src_bu: True if liquid at source should be drawn bottom-up.
            src_distance: Bottom-up / top-down distance at the source (mm).
            dst_flow: dispense speed at destination (0.05 mL/min <= src_flow <= 125 mL/min)
            dst_bu: True if liquid at destination should be dispensed bottom-up.
            dst_distance: Bottom-up / top-down distance at the destination (in mm).
            rinse_volume: Needle rinsing volume after action (mL)
            rinse_stn: Integer number of the rinse station (1 or 2).
            airgap: Airgap volume (mL)
            post_airgap: Post-airgap volume (mL)
            airgap_dst: Destination zone for airgap
            extra_volume: Extra volume (mL)
            extra_dst: Destination zone for extra volume
            equib_src: Equilibration time when drawing from source (s)
            equib_dst: Equilibration time when dispensing to destination (s)
            multiple_asp: True if multiple aspirations are allowed.
        """
        # Get different data types into uniform WellGroup data type
        source: WellGroup = WellGroup(source, well_configuration=self.wells, logger=self.logger)
        destination: WellGroup = WellGroup(destination, well_configuration=self.wells, logger=self.logger)

        # Update well states and information
        source.remove_liquid(quantity=volume)
        destination.add_liquid(quantity=volume)

        # Get correct rinse station
        if not needle == 0:
            rinse_stn = self.system_liquids[str(needle)]["rinse_station"]

        self.chemspeed.execute(
            'transfer_liquid',
            source_zone=str(source),
            destination_zone=str(destination),
            volume=volume,
            needle_no=needle,
            source_flow=src_flow,
            source_bottom_up=int(src_bu),
            source_distance=src_distance,
            destination_flow=dst_flow,
            destination_bottom_up=int(dst_bu),
            destination_distance=dst_distance,
            rinse_volume=rinse_volume,
            rinse_station=rinse_stn,
            airgap=airgap,
            post_airgap=post_airgap,
            airgap_destination=airgap_dst,
            extra_volume=extra_volume,
            extra_destination=extra_dst,
            equilibration_at_source=equib_src,
            equilibration_at_destination=equib_dst,
            multiple_aspirations=int(multiple_asp)
        )

    @deprecated(deprecated_in="1.0", removed_in="2.0",
                details="Deprecated. Use transfer_liquid instead, or refer to the routines sub-package.")
    def inject_liquid(self,
                      source: Zone,
                      destination: Zone,
                      volume: float,
                      src_flow: float = 10,
                      src_bu: float = 3,
                      dst_flow: float = 0.5,
                      dst_bu: float = 0,
                      rinse_volume: float = 2,
                      needle: int = 0,

                      ):
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
        self.transfer_liquid(
            source=source,
            destination=destination,
            volume=volume,
            needle=needle,
            src_flow=src_flow,
            src_bu=True,
            src_distance=src_bu,
            dst_flow=dst_flow,
            dst_bu=True,
            dst_distance=dst_bu,
            rinse_volume=rinse_volume
        )

    def transfer_solid(
            self,
            source: Zone,
            destination: Zone,
            weight: float,
            height: float = 0,
            chunk: float = 0.1,
            equilib: float = 5,
            rd_speed: float = 30,
            rd_acc: float = 20,
            rd_amp: float = 100,
            fd_amount: float = 1,
            fd_speed: float = 30,
            fd_acc: float = 20,
            fd_amp: float = 40,
            fd_num: float = 360
    ) -> List[float]:
        """Solid dispensing in Chemspeed.

        Args (float for non specified type):
            source (str, list): solid zone for transfer
            destination (str, list): zone for dispensing destination
            weight: weight to dispense (mg)
            height: dispense height relative to vial top, negative means into the vial (mm)
            chunk: rough dispensing chunk size (mg)
            equilib: equilibration time for balance (s)
            rd_speed: rough dispensing rotation speed (rpm)
            rd_acc: rough dispensing acceleration (s^-2)
            rd_amp: rough dispensing rotation amplitute (%)
            fd_amount: amount at the end for fine dispensing (mg)
            fd_speed: fine dispensing rotation speed (rpm)
            fd_acc: fine dispensing acceleration (s^-2)
            fd_amp: fine dispensing rotation amplitute (%)
            fd_num: fine dispensing angle (degree, 0-360)

        Returns:
            weights (list of float): real dispense weights (mg)
        """
        # Get different data types into uniform WellGroup data type
        source: WellGroup = WellGroup(source, well_configuration=self.wells, logger=self.logger)
        destination: WellGroup = WellGroup(destination, well_configuration=self.wells, logger=self.logger)

        # Update well states and information
        source.remove_solid(quantity=weight)
        destination.add_solid(quantity=0)

        self.chemspeed.execute(
            'transfer_solid',
            source_zone=str(source),
            destination_zone=str(destination),
            weight=weight,
            dispense_height=height,
            chunk_size=chunk,
            equilibration_time=equilib,
            rough_dispensing_speed=rd_speed,
            rough_dispensing_accuracy=rd_acc,
            rough_dispensing_amplitude=rd_amp,
            finde_dispensing_amount=fd_amount,
            fine_dispensing_speed=fd_speed,
            fine_dispensing_accuracy=fd_acc,
            finde_dispensing_amplitude=fd_amp,
            fine_dispensing_angle=fd_num
        )

        return [
            UnitConverter()("mass", float(mass), source_unit="kilo", target_unit="milli")
            for mass in self.chemspeed.return_data
        ]

    def transfer_solid_swile(
            self,
            source: Zone,
            destination: Zone,
            weight: float,
            height=0,
            chunk=0.2,
            equilib=2,
            depth=15,
            pickup=10,
            rd_step=1,
            fd_step=0.2,
            fd_amount=0.5,
            shake_angle=0.1,
            shake_time=2
    ):
    # TODO: Figure out what about the parameters shake_angle and shake_time
    #       They are currently still expected in the Manager.app

    # TODO: Properly test this function using a Manager configuration where the GDU can be mounted without colliding
    #       with the BALANCE zone.

        """Solid dispensing in Chemspeed (SWILE)

        Args (float for non specified type):
            source (str, list): solid zone for transfer
            destination (str, list): zone for dispensing destination
            weight: weight to dispense (mg)
            height: dispense height relative to vial top, negative means into the vial (mm)
            chunk: rough dispensing chunk size (mg)
            equilib: equilibration time for balance (s)
            depth: depth for the SWILE dipping into the power (mm)
            pickup: pickup volume in the swile (uL)
            rd_step: rough dispensing volume step size (uL)
            fd_step: find dispensing volume step size (uL)
            fd_amount: amount to start fine dispensing (mg)
            shake_angle: source vial shaking angle (rad)
            shake_time: source vial shaking time (s)
        """

        raise NotImplementedError("This function has never been properly tested on the Manager or the hardware, and"
                                  "can therefore not be executed via the Python controller at the current stage. ")

        # Get different data types into uniform WellGroup data type
        source: WellGroup = WellGroup(source, well_configuration=self.wells, logger=self.logger)
        destination: WellGroup = WellGroup(destination, well_configuration=self.wells, logger=self.logger)

        # Update well states and information
        source.remove_solid(quantity=weight)
        destination.add_solid(quantity=0)

        self.chemspeed.execute(
            'transfer_solid_swile',
            source_zone=str(source),
            destination_zone=str(destination),
            weight=weight,
            height=height,
            chunk_size=chunk,
            equilibration_time=equilib,
            depth=depth,
            pickup_volume=pickup,
            rough_dispensing_step_size=rd_step,
            fine_dispensing_step_size=fd_step,
            fine_dispensing_amount=fd_amount,
            shake_time=shake_time,
            shake_angle=shake_angle
        )

    def set_drawer(
            self,
            zone: Zone,
            state: str,
            environment: str = 'none'
    ):
        """
        Setting ISYNTH drawer position. For accessing the vials in ISYNTH.
        Can set the vials under vacuum, inert or none state.

        Args:
            zone (str, list): zones for setting drawer state, has to be in ISYNTH
            state (str): drawer open state (open, close)
            environment (str): environment state the zone will be in (inert, vacuum, none)
        """
        zone = WellGroup(zone, well_configuration=self.wells, logger=self.logger)
        zone.set_parameter("drawer", state)
        zone.set_parameter("environment", environment)

        self.chemspeed.execute(
            'set_drawer',
            zone=str(zone),
            state=state,
            environment=environment
        )

    @deprecated(deprecated_in="chemspyd-1.0", removed_in="chemspyd-2.0",
                details="ISYNTH-specific methods will be deprecated. Use set_reflux instead.")
    def set_isynth_reflux(
            self,
            state: str,
            temperature: float = 15
    ) -> None:
        """Setting ISYNTH reflux chilling temperature.

        Args:
            state (str): cryostat state (on, off)
            temperature (float): temperature to set at when cryostat is on (C)
        """
        self.set_reflux("ISYNTH:1", state, temperature)

    def set_reflux(
            self,
            reflux_zone: Zone,
            state: str,
            temperature: float = 0
    ) -> None:
        """
        Sets the reflux chilling temperature on a defined zone.

        Args:
            reflux_zone: Zone to be refluxed
            state: Cryostat state (on, off)
            temperature: Temperature (in °C) to set the cryostat to.
        """
        reflux_zone = WellGroup(reflux_zone, self.wells, logger=self.logger)
        reflux_zone.set_parameter("reflux", state)
        reflux_zone.set_parameter("reflux_temperature", temperature)

        self.chemspeed.execute(
            "set_reflux",
            zone=reflux_zone.get_element_string(),
            state=state,
            temperature=temperature
        )

    @deprecated(deprecated_in="chemspyd-1.0", removed_in="chemspyd-2.0",
                details="ISYNTH-specific methods will be deprecated. Use set_temperature instead.")
    def set_isynth_temperature(
            self,
            state: str,
            temperature: float = 15,
            ramp: float = 0
    ) -> None:
        """Setting ISYNTH heating temperature.

        Args:
            state (str): cryostat state (on, off)
            temperature (float): temperature to set at when cryostat is on (C)
            ramp (float): ramping speed for the temperature (C/min)
        """
        self.set_temperature("ISYNTH:1", state, temperature, ramp)

    def set_temperature(
            self,
            temp_zone: Zone,
            state: str,
            temperature: float = 20,
            ramp: float = 0
    ) -> None:
        """
        Sets the heating temperature for a given element.

        Args:
            temp_zone: Zone to be heated / cooled (ISYNTH, RACK_HS)
            state: Cryostat state (on, off)
            temperature: Temperature (in °C) to set the cryostat to.
            ramp: Ramping speed for the temperature (in °C / min)
        """
        temp_zone = WellGroup(temp_zone, self.wells, logger=self.logger)
        temp_zone.set_parameter("thermostat", state)
        temp_zone.set_parameter("thermostat_temperature", temperature)
        temp_zone.set_parameter("thermostat_ramp", ramp)

        self.chemspeed.execute(
            "set_temperature",
            zone=str(temp_zone),
            state=state,
            temperature=temperature,
            ramp_speed=ramp
        )

    @deprecated(deprecated_in="chemspyd-1.0", removed_in="chemspyd-2.0",
                details="ISYNTH-specific methods will be deprecated. Use set_stir instead.")
    def set_isynth_stir(
            self,
            state: str,
            rpm: float = 200
    ) -> None:
        """Setting ISYNTH vortex speed.

        Args:
            state (str): vortex state (on, off)
            rpm (float): vortex rotation speed (rpm)
        """
        self.set_stir("ISYNTH:1", state, rpm)

    def set_stir(
            self,
            stir_zone: Zone,
            state: str,
            rpm: float = 0
    ) -> None:
        """
        Set stirring.

        Args:
            stir_zone (str): Wells to be stirred
            state (str): stir state (on, off)
            rpm (float): stir rotation speed (rpm)
        """
        stir_zone = WellGroup(stir_zone, self.wells, logger=self.logger)
        stir_zone.set_parameter("stir", state)
        stir_zone.set_parameter("stir_rate", rpm)

        self.unmount_all()
        self.chemspeed.execute(
            'set_stir',
            zone=stir_zone.get_element_string(),
            state=state,
            stir_rate=rpm
        )

    @deprecated(deprecated_in="chemspyd-1.0", removed_in="chemspyd-2.0",
                details="ISYNTH-specific methods will be deprecated. Use set_vacuum instead.")
    def set_isynth_vacuum(
            self,
            state: str,
            vacuum: float = 1000
    ) -> None:
        """Setting ISYNTH vacuum pressure.

        Args:
            state (str): vacuum pump state (on, off)
            vacuum (float): vacuum pressure level (mbar)
        """
        self.set_vacuum("ISYNTH:1", state, vacuum)

    def set_vacuum(
            self,
            vac_zone: Zone,
            state: str,
            vacuum: float = 1000
    ) -> None:
        """
        Sets the heating temperature for a given element.

        Args:
            vac_zone: Zone to be set under vacuum
            state: Vacuum pump state state (on, off)
            vacuum: Pressure to set the vacuum pump to (in mbar).
        """
        vac_zone = WellGroup(vac_zone, self.wells, logger=self.logger)
        vac_zone.set_parameter("vacuum_pump", state)
        vac_zone.set_parameter("vacuum_pump_pressure", vacuum)
        self.chemspeed.execute(
            "set_vacuum",
            zone=vac_zone.get_element_string(),
            state=state,
            pressure=vacuum
        )

    @deprecated(deprecated_in="chemspyd-1.0", removed_in="chemspyd-2.0",
                details="ISYNTH-specific methods will be deprecated. Use operation-specific methods instead.")
    def set_isynth(
            self,
            **kwargs: Optional[Union[str, float]]
    ) -> None:
        """Setting ISYNTH values. The following values can be [None, str, float]. If set at None, no change to current state.
        If "off" then turns off. If set to a value, then the system will turn on and set to that value.
        You have to specify the values to be set. For example, set_isynth(reflux=15) not set_isynth(15).

        Args:
            reflux: vacuum pressure level (C)
            temperature: vacuum pressure level (C)
            stir: vacuum pressure level (rpm)
            vacuum: vacuum pressure level (mbar)
        """
        for key in ['reflux', 'temperature', 'stir', 'vacuum']:
            value = kwargs.get(key, None)
            if value is None:
                pass
            elif value == 'off':
                method = getattr(self, f'set_isynth_{key}')
                method(state='off')
            else:
                method = getattr(self, f'set_isynth_{key}')
                method('on', value)
        return

    def vial_transport(
            self,
            source: str,
            destination: str,
            gripping_force: float = 10,
            gripping_depth: float = 7.5,
            push_in: bool = False,
            grip_inside: bool = False
    ) -> None:
        """ Vial Transport

        Args (float for non specified type):
            source: vial zone for transfer
            destination: zone for vial destination
            gripping_force: gripping force for picking up the vials (N)
            gripping_depth: gripping depth for the distance (down) to picking it up (mm)
            push_in: False if the vial should be dropped into the position (for the last mm)
            grip_inside: True if the vial should be gripped from the inside of the neck.
        """
        source = WellGroup(source, well_configuration=self.wells, logger=self.logger)
        destination = WellGroup(destination, well_configuration=self.wells, logger=self.logger)
        self.chemspeed.execute(
            'vial_transport',
            source_zone=str(source),
            destination_zone=str(destination),
            gripping_force=gripping_force,
            gripping_depth=gripping_depth,
            push_vial_in=int(push_in),
            grip_inside=int(grip_inside)
        )

    def set_zone_state(
            self,
            zone: Zone,
            state: bool = True
    ) -> None:
        """Setting the 'Enabled' state of the zone. Certain operations may turn off the availability of a zone.
        Use this to re-enable. For example, solid dispensing error may result in disabling the powder container to be used.

        Args:
            zone (str, list): zones to change the state
            state (bool): Enable or disable (True, False)
        """
        zone = WellGroup(zone, well_configuration=self.wells, logger=self.logger)
        self.chemspeed.execute(
            'set_zone_state',
            zone=str(zone),
            state=int(state)
        )

    def measure_level(
            self,
            zone: Zone
    ) -> List[float]:
        """Measure material level.

        Args:
            zone (Zone): zones to measure
        """
        zone = WellGroup(zone, well_configuration=self.wells, logger=self.logger)
        self.chemspeed.execute(
            'measure_level',
            zone=str(zone))
        return [float(level) for level in self.chemspeed.return_data]

    def unmount_all(self):
        """Unmounting all equipment from the arm"""
        self.chemspeed.execute('unmount_all')

    def stop_manager(self):
        """Stopping the manager safely from the python controller"""
        self.chemspeed.execute('stop_manager')

    def read_status(
            self,
            key: Optional[str] = None
    ) -> Union[Dict[str, float], float]:
        """Reading the Chemspeed status during idle.

        Args:
            key (None, str): Status to read (from the specified keys in self.status_keys)

        Returns:
            values: single float value of the key. dict if no key specified.
            units: cryostat, chiller in C; vacuum in mbar, vortex in rpm
        """
        status: dict = {}

        for parameter, status_value in zip(self.status_keys, self.chemspeed.status):
            value: float = UnitConverter()(
                parameter_type=parameter,
                value=float(status_value),
                source_unit=self.status_keys[parameter]["source_unit"],
                target_unit=self.status_keys[parameter]["target_unit"]
            )
            status[parameter] = value

        if key in status:
            return status[key]
        else:
            return status

    def wait(
            self,
            duration: Union[int, float]
    ) -> None:
        """
        Waits for a set duration of time by calling the "wait" method of AutoSuite.

        Args:
            duration: Duration of wait (in seconds)
        """
        self.chemspeed.execute(
            "wait",
            time=duration
        )
