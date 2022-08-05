from typing import Dict, List, Union
import os
from pathlib import Path
import time
from deprecation import deprecated

from chemspyd.utils.logging_utils import get_logger
import chemspyd.utils.unit_conversions as units
from chemspyd.utils import load_json, read_csv, write_csv
from chemspyd.zones import Zone, WellGroup, initialize_zones

if os.name == 'nt':
    import msvcrt


class ChemspeedController(object):
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
            stdout: bool = True,
            logfile: Union[str, Path, None] = None,
            simulation: bool = False,
            track_quantities: bool = False
    ) -> None:
        """
        Initializes the ChemspeedController by:
            - setting up the paths to the communication files
            - establishing logging

        Args:
            cmd_folder: Path to the folder containing the csv files for communicating with the instrument.
            element_config: Path to the .json file containing the configuration of the ChemspeedElements.
            system_liquids: Path to the .json file containing the configuration of the pumps and system liquids.
            stdout: True if logging output should be displayed on the console.
            logfile: Path to the log file. If None, no log file is written.
            simulation: True in order to run the Python controller (not Autosuite!) in simulation mode.
                        Will only print execution statements then (without sending any commands to the instrument).
            track_quantities: True if vial volumes should be rigorously tracked.

        """
        self.cmd_file = Path(cmd_folder) / "command.csv"
        self.rsp_file = Path(cmd_folder) / "response.csv"
        self.sts_file = Path(cmd_folder) / "status.csv"
        self.ret_file = Path(cmd_folder) / "return.csv"

        self.logger = get_logger(stdout, logfile)

        self.simulation = simulation

        self.system_liquids: dict = load_json(system_liquids)
        self.elements, self.wells = initialize_zones(load_json(element_config), track_quantities)


    #############################
    # Chemspeed Remote Statuses #
    #############################

    def _chemspeed_idle(self) -> bool:
        """
        Checks for the instrument to be idle.

        Returns:
            bool: True if the instrument is idle, else False.
        """
        rsp_readout: list = read_csv(self.rsp_file, single_line=True)
        return rsp_readout[0] == "1"

#         with open(self.rsp_file, 'r') as f:
#            line = f.readline()
#        message = line.split(',')
#        return message[0] == '1'

    def _chemspeed_newcmd(self) -> bool:
        """
        Checks if the instrument has received a new command.

        Returns:
            bool: True if it has received a new command, else False.
        """
        cmd_readout: list = read_csv(self.cmd_file, single_line=True)
        return cmd_readout[0] == "1"

#        with open(self.cmd_file, 'r') as f:
#            line = f.readline()
#        message = line.split(',')
#        return message[0] == '1'

    def chemspeed_blocked(self) -> bool:
        """
        Checks if the instrument is blocked, i.e.
            - not idle
            - has received a new command

        Returns:
            bool: True if the instrument is blocked, else False.
        """
        return not self._chemspeed_idle() or self._chemspeed_newcmd()

    ###############################
    # Low Level Command Execution #
    ###############################

    def execute(self, command: str, *args) -> None:
        """
        Main method to execute a given operation.
        Writes the command into the command.csv file, including the command name and all required arguments.

        Args:
            command (str): The command name to be received in Chemspeed.
            *args: List of arguments for the command.
        """
        args_line = ','.join([str(arg) for arg in args])
        exec_message = f"Execute: {command}({args_line.replace(',', ', ')})"

        # skip everything if simulation
        if self.simulation:
            self.logger.debug(exec_message)
            return

        # send to file
        while self.chemspeed_blocked():
            time.sleep(0.1)
        write_csv([[1, command], [args_line, "end"]], file_name=self.cmd_file)
        # with open(self.cmd_file, 'w') as f:
            # set new command to true, and the command name
        #    f.write(f"1,{command}\n")
        #    f.write(f'{args_line},end')

        # stdout & logging
        self.logger.info(exec_message, extra={"continue_line": True})

        # wait until no idle to confirm that the command was executed
        while self._chemspeed_idle():
            time.sleep(0.1)
        self.logger.debug("-> started", extra={"format": False})

        # self block, optional, or change to error detection
        while self.chemspeed_blocked():
            time.sleep(0.1)

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
            dst_distance: float = 0,
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
        # ATTN: API Broken compared to ChemsPyd 0.2!

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
        source_wells: WellGroup = WellGroup(source, well_configuration=self.wells)
        destination_wells: WellGroup = WellGroup(destination, well_configuration=self.wells)

        # Update well states and information
        source_wells.remove_material(quantity=volume)
        destination_wells.add_material(quantity=volume)

        # Get correct rinse station
        # TODO: Figure out if this is the best way to handle the case of needle = 0  -> default rinse station
        if not needle == 0:
            rinse_stn = self.system_liquids[str(needle)]["rinse_station"]

        self.execute(
            'transfer_liquid',
            source_wells.get_zone_string(),
            destination_wells.get_zone_string(),
            volume,
            needle,
            src_flow,
            int(src_bu),
            src_distance,
            dst_flow,
            int(dst_bu),
            dst_distance,
            rinse_volume,
            rinse_stn,
            airgap,
            post_airgap,
            airgap_dst,
            extra_volume,
            extra_dst,
            equib_src,
            equib_dst,
            int(multiple_asp)
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
        source_wells: WellGroup = WellGroup(source, well_configuration=self.wells)
        destination_wells: WellGroup = WellGroup(destination, well_configuration=self.wells)

        # Update well states and information
        source_wells.remove_material(quantity=weight)
        destination_wells.add_material(quantity=0)

        self.execute(
            'transfer_solid',
            source_wells.get_zone_string(),
            destination_wells.get_zone_string(),
            weight,
            height,
            chunk,
            equilib,
            rd_speed,
            rd_acc,
            rd_amp,
            fd_amount,
            fd_speed,
            fd_acc,
            fd_amp,
            fd_num
        )
        weights: list = read_csv(self.ret_file, single_line=True)
        return [units.convert_mass(mass, dst="milli") for mass in weights[:-1]]

#        with open(self.ret_file, 'r') as f:
#            weights_str = f.readline().split(',')[:-1]
#        return [float(w) * 1e6 for w in weights_str]

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
            # shake_angle=0.1,
            # shake_time=2
    ):
    # TODO: Figure out what about the parameters shake_angle and shake_time
    #       They are currently still expected in the Manager.app

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
        # Get different data types into uniform WellGroup data type
        source_wells: WellGroup = WellGroup(source, well_configuration=self.wells)
        destination_wells: WellGroup = WellGroup(destination, well_configuration=self.wells)

        # Update well states and information
        source_wells.remove_material(quantity=weight)
        destination_wells.add_material(quantity=0)

        self.execute(
            'transfer_solid_swile',
            source_wells.get_zone_string(),
            destination_wells.get_zone_string(),
            weight,
            height,
            chunk,
            equilib,
            depth,
            pickup,
            rd_step,
            fd_step,
            fd_amount
        )

    def set_drawer(
            self,
            zone: Zone,
            state: str, environment: str = 'none'
    ):
        """
        Setting ISYNTH drawer position. For accessing the vials in ISYNTH.
        Can set the vials under vacuum, inert or none state.

        Args:
            zone (str, list): zones for setting drawer state, has to be in ISYNTH
            state (str): drawer open state (open, close)
            environment (str): environment state the zone will be in (inert, vacuum, none)
        """
        zone = WellGroup(zone, well_configuration=self.wells)
        zone.set_parameter("drawer", state)
        zone.set_parameter("environment", environment)

        self.execute(
            'set_drawer',
            zone.get_zone_string(),
            state,
            environment
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
        reflux_zone = WellGroup(reflux_zone, self.wells)
        reflux_zone.set_parameter("reflux", state)
        reflux_zone.set_parameter("reflux_temperature", temperature)

        self.execute(
            "set_reflux",
            reflux_zone.get_element_string(),
            state,
            temperature
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
        temp_zone = WellGroup(temp_zone, self.wells)
        temp_zone.set_parameter("thermostat", state)
        temp_zone.set_parameter("thermostat_temperature", temperature)
        temp_zone.set_parameter("thermostat_ramp", ramp)

        self.execute(
            "set_temperature",
            temp_zone.get_zone_string(),
            state,
            temperature,
            ramp
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
        stir_zone = WellGroup(stir_zone, self.wells)
        stir_zone.set_parameter("stir", state)
        stir_zone.set_parameter("stir_rate", rpm)

        self.unmount_all()
        self.execute(
            'set_stir',
            stir_zone.get_element_string(),
            state,
            rpm
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

#        self.elements["ISYNTH"].validate_parameter("vacuum_pump", state)
#        self.elements["ISYNTH"].validate_parameter("vacuum_pump_pressure", vacuum)

#        self.execute(
#            'set_isynth_vacuum',
#            state,
#            vacuum
#        )

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
            vacuum: Pressure to set the vacuum pump to.
        """
        vac_zone = WellGroup(vac_zone, self.wells)
        vac_zone.set_parameter("vacuum_pump", state)
        vac_zone.set_parameter("vacuum_pump_pressure", vacuum)
        self.execute(
            "set_vacuum",
            vac_zone.get_element_string(),
            state,
            vacuum
        )

    @deprecated(deprecated_in="chemspyd-1.0", removed_in="chemspyd-2.0",
                details="ISYNTH-specific methods will be deprecated. Use operation-specific methods instead.")
    def set_isynth(
            self,
            **kwargs: Union[None, str, float]
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
            push_in: bool = True
    ) -> None:
        """ Vial Transport

        Args (float for non specified type):
            source (str, list): vial zone for transfer
            destination (str, list): zone for vial destination
            gripping_force (float): gripping force for picking up the vials (N)
            gripping_depth (float): gripping depth for the distance (down) to picking it up (mm)
        """
        # TODO: exclude crashing for certain zones
        # ATTN: Function has never been tested properly on the Manager.app or even on the ChemSpeed!!!
        source = WellGroup(source, well_configuration=self.wells)
        destination = WellGroup(destination, well_configuration=self.wells)
        self.execute(
            'vial_transport',
            source.get_zone_string(),
            destination.get_zone_string(),
            gripping_force,
            gripping_depth,
            int(push_in)
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
        zone = WellGroup(zone, well_configuration=self.wells)
        self.execute(
            'set_zone_state',
            zone.get_zone_string(),
            int(state)
        )

    def measure_level(
            self,
            zone: Zone
    ) -> List[float]:
        """Measure material level.

        Args:
            zone (Zone): zones to measure
        """
        zone = WellGroup(zone, well_configuration=self.wells)
        self.execute('measure_level', zone.get_zone_string())

        levels: list = read_csv(self.ret_file, single_line=True)
        return [float(level) for level in levels[:-1]]

#        with open(self.ret_file, 'r') as f:
#            levels_str = f.readline().split(',')[:-1]
#        return [float(level) for level in levels_str]

    def unmount_all(self):
        """Unmounting all equipment from the arm"""
        self.execute('unmount_all')

    def stop_manager(self):
        """Stopping the manager safely from the python controller"""
        self.execute('stop_manager')

    def read_status(
            self,
            key: Union[None, str] = None
    ) -> Union[Dict[str, float], float]:
        """Reading the Chemspeed status during idle.

        Args:
            key (None, str): status to read ['temperature', 'reflux', 'vacuum', 'stir', 'box_temperature']

        Returns:
            values: single float value of the key. dict if no key specified.
            units: cryostat, chiller in C; vacuum in mbar, vortex in rpm
        """
        readout_data_units: dict = {
            "temperature": units.temp_k_to_c,
            "reflux": units.temp_k_to_c,
            "vacuum": units.pressure_pa_to_mbar,
            "stir": units.no_change,
            "box_temperature": units.temp_k_to_c,
            "box_humidity": units.no_change
        }

#        with open(self.sts_file, 'r') as f:
#            line = f.readline()[:-1]

        values: list = read_csv(self.sts_file, single_line=True)[:-1]

        status: dict = {parameter: readout_data_units[parameter](float(value)) for parameter, value in zip(readout_data_units, values)}

        if key in readout_data_units:
            return status[key]
        else:
            return status

    def wait(
            self,
            duration: int
    ) -> None:
        """
        waits for a set duration
        can be cancelled by hitting q
        Args:
            duration: duration of wait (in seconds)

        Returns: None
        """
        self.logger.info(f"Waiting for {duration} seconds.")
        if not self.simulation:
            print('press "q" to cancel wait')
            while duration >= 0:
                print("", end=f'\rWaiting for {duration} seconds.')
                time.sleep(1)
                duration -= 1
                if os.name == 'nt':
                    # FIXME: Temporarily putting a type ignore here. Should fix to also allow
                    #  catching keyboard input from other OSs.
                    # FIXME: Should this be a global variable function that is set / imported with the OS?
                    if msvcrt.kbhit() and msvcrt.getwch() == 'q':  # type: ignore[attr-defined]
                        self.logger.info("Wait cancelled.")
                        break

        self.logger.info(f"Waiting for {duration} seconds completed.")

    # TODO: Screwcapping is currently included as a method in the Manager.app
    #       However, it is not really implemented there...
    #       Do we want it? Do we need it?
