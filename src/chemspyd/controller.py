from typing import Dict, List, Union
import os
import time
from deprecation import deprecated

import chemspyd.utils.unit_conversions as units
from chemspyd.defaults import *
from chemspyd.utils import load_json
from chemspyd.zones import Zone, WellGroup, initialize_zones

if os.name == 'nt':
    import msvcrt


class ChemspeedController:
    """Controller class for the Chemspeed platform.

    Args:
        cmd_folder: the folder path containing CSV files for communication with the platform.
        stdout: disable commandline output messages.
        logfile: log file path.
        simulation: True to run the controller in simulation (only in python, not autosuite).
    """

    def __init__(self,
                 cmd_folder: str,  # TODO: Change to Path?
                 element_config: Union[dict, None] = None,
                 system_liquids: Union[dict, None] = None,
                 stdout: bool = True,
                 logfile: str = '',  # TODO: Change to Path?
                 simulation: bool = False,
                 track_quantities: bool = False
                 ) -> None:
        """Initialize paths to files for communication with the platform."""
        # ATTN: Need to figure out if Path will work with //IPC/... path.
        self.cmd_file = os.path.join(cmd_folder, 'command.csv')
        self.rsp_file = os.path.join(cmd_folder, 'response.csv')
        self.sts_file = os.path.join(cmd_folder, 'status.csv')
        self.ret_file = os.path.join(cmd_folder, 'return.csv')
        self.stdout = stdout
        self.logfile = logfile
        self.simulation = simulation

        if not element_config:
            element_config: dict = load_json(DEFAULTS_PATH / "element_config.json")
        if not system_liquids:
            system_liquids = load_json(DEFAULTS_PATH / "system_liquids.json")
        self.system_liquids: dict = system_liquids
        self.elements, self.wells = initialize_zones(element_config, track_quantities)

    #############################
    # Chemspeed Remote Statuses #
    #############################

    def _chemspeed_idle(self):
        with open(self.rsp_file, 'r') as f:
            line = f.readline()
        message = line.split(',')
        return message[0] == '1'

    def _chemspeed_newcmd(self):
        with open(self.cmd_file, 'r') as f:
            line = f.readline()
        message = line.split(',')
        return message[0] == '1'

    def chemspeed_blocked(self):
        # blocked in cases of:
        # >> not idle
        # >> chemspeed received new command
        return not self._chemspeed_idle() or self._chemspeed_newcmd()

    ###############################
    # Low Level Command Execution #
    ###############################

    def execute(self, command: str, *args) -> None:
        """Method that alters the command CSV for Chemspeed, includes command name and arguments.
        Args:
            command (str): The command name to be received in Chemspeed.
            *args: List of arguments for the command.
        """
        args_line = ','.join([str(arg) for arg in args])
        exec_message = f"Execute: {command}({args_line.replace(',', ', ')})"

        # skip everything if simulation
        if self.simulation:
            print(exec_message)
            return

        # send to file
        while self.chemspeed_blocked():
            time.sleep(0.1)
        with open(self.cmd_file, 'w') as f:
            # set new command to true, and the command name
            f.write(f"1,{command}\n")
            f.write(f'{args_line},end')

        # stdout & logging
        exec_message = f"Execute: {command}({args_line.replace(',', ', ')})"
        if self.stdout:
            print(exec_message, end='', flush=True)
        if self.logfile != '':
            with open(self.logfile, 'a') as f:
                f.write(f"{exec_message}\n")

        # wait until no idle to print command executed
        while self._chemspeed_idle():
            time.sleep(0.1)
        if self.stdout:
            print(' -> started')

        # self block, optional, or change to error detection
        while self.chemspeed_blocked():
            time.sleep(0.1)

    ##################################
    # High Level Chemspeed Functions #
    ##################################

    def transfer_liquid(
            self,
            source: Zone,
            destination: Zone,
            volume: float,
            src_flow: float = 10,
            dst_flow: float = 10,
            src_bu: float = 3,
            dst: float = 0,
            rinse_volume: float = 2,
            needle: int = 0,
            airgap: float = 0.01,
            post_airgap: float = 0,
            extra_volume: float = 0,
            airgap_dst: Zone = 'WASTE',
            extra_dst: Zone = 'WASTE',
            equib_src: float = 0,
            equib_dst: float = 0,
            rinse_stn: int = 1,
            multiple_asp: bool = False,
            bu: bool = False
    ):
        """Transfer liquid in Chemspeed.

        Args (float for non specified type):
            source (str, list): zone for transfer source
            destination (str, list): zone for destination of transfer
            volume: volume to transfer (0 mL <= volume <= 20 mL)
            src_flow: draw speed at source (0.05 mL/min <= src_flow <= 125 mL/min)
            dst_flow: dispense speed at destination (0.05 mL/min <= src_flow <= 125 mL/min)
            src_bu: needle bottoms up distance at source (mm)
            dst: needle distance at destination (mm)
            rinse_volume: needle rinsing volume after action (mL)
            needle: the limited needle to use, 0 means select all, 12 means needles 1 and 2
            airgap: airgap volume (mL)
            post_airgap: post-airgap volume (mL)
            extra_volume: extra volume (mL)
            airgap_dst: destination zone for airgap (zone)
            extra_dst: destination zone for extra volume (zone)
            euqib_src: equilibration time when drawing from source (s)
            equib_dst: equilibration time when dispensing to destination (s)
            rinse_stn: rinse station corresponding to Waste 1 or Waste 2
            multi_asp: whether multiple aspirations are allowed
            bu: true if dst is bottom-up, false if

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
            src_flow,
            dst_flow,
            src_bu,
            dst,
            rinse_volume,
            needle,
            airgap,
            post_airgap,
            extra_volume,
            airgap_dst,
            extra_dst,
            equib_src,
            equib_dst,
            rinse_stn,
            int(multiple_asp),
            int(bu)
        )

    # def transfer_liquid_bu(
    #     self,
    #     source: Zones,
    #     destination: Zones,
    #     volume: float,
    #     src_flow: float = 10,
    #     dst_flow: float = 10,
    #     src_bu: float = 3,
    #     dst_bu: float = 0,
    #     rinse_volume: float = 2,
    #     needle: int = 0,
    #     airgap: float = 0.01,
    #     post_airgap: float = 0,
    #     extra_volume: float = 0,
    #     airgap_dst: Zones = 'WASTE',
    #     extra_dst: Zones = 'WASTE',
    #     equib_src: float = 0,
    #     equib_dst: float = 0,
    #     rinse_stn: int = 1,
    #     multiple_aspirations: bool = False
    # ):
    #     """Transfer liquid in Chemspeed. Destination bottoms up version. Commonly used in injection valves.
    #
    #     Args (float for non specified type):
    #         source (str, list): zone for transfer source
    #         destination (str, list): zone for destination of transfer
    #         volume: volume to transfer (mL)
    #         src_flow: draw speed at source (mL/min)
    #         dst_flow: dispense speed at destination (mL/min)
    #         src_bu: needle bottoms up distance at source (mm)
    #         dst_bu: needle bottoms up distance at destination (mm)
    #         rinse_volume: needle rinsing volume after action (mL)
    #         needle: the limited needle to use, 0 means select all
    #     """
    #     source = to_zone_string(source)
    #     destination = to_zone_string(destination)
    #     self.execute(
    #         'transfer_liquid_bu',
    #         source,
    #         destination,
    #         volume,
    #         src_flow,
    #         dst_flow,
    #         src_bu,
    #         dst_bu,
    #         rinse_volume,
    #         needle,
    #         airgap,
    #         post_airgap,
    #         extra_volume,
    #         airgap_dst,
    #         extra_dst,
    #         equib_src,
    #         equib_dst,
    #         rinse_stn,
    #         int(multiple_aspirations)
    #     )

    # TODO: Deprecation error/warning/workaround...
    def inject_liquid(self,
                      source: Zone,
                      destination: Zone,
                      volume: float,
                      src_flow: float = 10,
                      src_bu: float = 3,
                      dst_flow: float = 0.5,
                      dst_bu: float = 0,
                      rinse_volume: float = 2,
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
        # Get different data types into uniform WellGroup data type
        source_wells: WellGroup = WellGroup(source, well_configuration=self.wells)
        destination_wells: WellGroup = WellGroup(destination, well_configuration=self.wells)

        # Update well states and information
        source_wells.remove_material(quantity=volume)
        destination_wells.add_material(quantity=volume)

        self.execute(
            'inject_liquid',
            source_wells.get_zone_string(),
            destination_wells.get_zone_string(),
            volume,
            src_flow,
            src_bu,
            dst_flow,
            dst_bu,
            rinse_volume,
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
        with open(self.ret_file, 'r') as f:
            weights_str = f.readline().split(',')[:-1]
        return [float(w) * 1e6 for w in weights_str]

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
        self.elements["ISYNTH"].validate_parameter("reflux", state)
        self.elements["ISYNTH"].validate_parameter("reflux_temperature", temperature)

        self.execute(
            'set_isynth_reflux',
            state,
            temperature
        )

    def set_reflux(
            self,
            reflux_zone: Zone,
            state: str,
            temperature: float = 0
    ) -> None:
        """
        Sets the reflux chilling temperature on a defined zone.

        ATTN: Currently implemented in analogy to the set_stir method.
                - the reflux_zone argument is not c

        Args:
            reflux_zone: Zone to be refluxed (ISYNTH)
            state: Cryostat state (on, off)
            temperature: Temperature (in °C) to set the cryostat to.
        """
        raise NotImplementedError
        # TODO: Implement the proper set_reflux function on the Manager.
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
        self.elements["ISYNTH"].validate_parameter("thermostat", state)
        self.elements["ISYNTH"].validate_parameter("thermostat_temperature", temperature)
        self.elements["ISYNTH"].validate_parameter("thermostat_ramp", ramp)

        self.execute(
            'set_isynth_temperature',
            state,
            temperature,
            ramp
        )

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
        raise NotImplementedError
        # TODO: Implement the proper set_temperature function on the Manager.
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
        self.elements["ISYNTH"].validate_parameter("stir", state)
        self.elements["ISYNTH"].validate_parameter("stir_rate", rpm)

        self.execute(
            'set_isynth_stir',
            state,
            rpm
        )

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
        self.elements["ISYNTH"].validate_parameter("vacuum_pump", state)
        self.elements["ISYNTH"].validate_parameter("vacuum_pump_pressure", vacuum)

        self.execute(
            'set_isynth_vacuum',
            state,
            vacuum
        )

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
        raise NotImplementedError
        # TODO: Implement the proper set_vacuum function on the Manager.
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
        source = WellGroup(source, well_configuration=self.wells)
        destination = WellGroup(destination, well_configuration=self.wells)
        self.execute(
            'vial_transport',
            source.get_zone_string(),
            destination.get_zone_string(),
            gripping_force,
            gripping_depth,
            push_in
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

        with open(self.ret_file, 'r') as f:
            levels_str = f.readline().split(',')[:-1]
        return [float(level) for level in levels_str]

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
        with open(self.sts_file, 'r') as f:
            line = f.readline()[:-1]
        values = list(map(float, line.split(',')))
        convert = [
            units.temp_k_to_c,
            units.temp_k_to_c,
            units.pressure_pa_to_mbar,
            units.no_change,
            units.temp_k_to_c,
            units.no_change,
        ]
        types = ['temperature', 'reflux', 'vacuum', 'stir', 'box_temperature', 'box_humidity']
        status = {t: c(v) for t, v, c in zip(types, values, convert)}
        if key in types:
            return status.get(key, None)
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
            duration: duration of wait

        Returns: None
        """
        dur = duration
        if self.simulation:
            print("Waiting for 0 seconds")
        else:
            print('press "q" to cancel wait')
            while duration >= 0:
                print("", end=f'\rWaiting for {duration} seconds.')
                time.sleep(1)
                duration -= 1
                if os.name == 'nt':
                    # FIXME: Temporarily putting a type ignore here. Should fix to also allow
                    #  catching keyboard input from other OSs.
                    if msvcrt.kbhit() and msvcrt.getwch() == 'q':  # type: ignore[attr-defined]
                        print("\nWait cancelled")
                        # FIXME: Shouldn't this be a break?
                        duration = -1

        print(f'Finished waiting for {dur} seconds')
