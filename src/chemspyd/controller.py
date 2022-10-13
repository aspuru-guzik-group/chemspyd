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
            needle: int,
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
        Executes a liquid transfer from the source to the target zone.
        Uses the 'Transfer Volumetrically' method in AutoSuite.

        Args:
            source: Source zone for the liquid transfer.
            destination: Destination zone for the liquid transfer.
            volume: Volume to transfer [mL]
            needle: Number of the needle to use (0 means all needles).
            src_flow: Draw speed at the source [mL/min] (0.05 mL/min <= src_flow <= 125 mL/min)
            src_bu: True if liquid at source should be drawn bottom-up.
            src_distance: Needle bottom-up / top-down distance at the source [mm].
            dst_flow: Dispense speed at destination [mL/min] (0.05 mL/min <= src_flow <= 125 mL/min)
            dst_bu: True if liquid at destination should be dispensed bottom-up.
            dst_distance: Needle bottom-up / top-down distance at the destination [mm].
            rinse_volume: Needle rinsing volume after action [mL]
            rinse_stn: Integer number of the rinse station.
            airgap: Airgap volume [mL]
            post_airgap: Post-airgap volume [mL]
            airgap_dst: Destination zone for airgap
            extra_volume: Extra volume [mL]
            extra_dst: Destination zone for extra volume
            equib_src: Equilibration time when drawing from source [s]
            equib_dst: Equilibration time when dispensing to destination [s]
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
            **{
                "Source Zone": {"value": str(source), "unit": None},
                "Destination Zone": {"value": str(destination), "unit": None},
                "Volume": {"value": volume, "unit": "mL"},
                "Needle No.": {"value": needle, "unit": None},
                "Flow Rate (Source)": {"value": src_flow, "unit": "mL/min"},
                "Bottom-Up (Source)": {"value": int(src_bu), "unit": None},
                "Distance (Source)": {"value": src_distance, "unit": "mm"},
                "Flow Rate (Destination)": {"value": dst_flow, "unit": "mL/min"},
                "Bottom-Up (Destination)": {"value": int(dst_bu), "unit": None},
                "Distance (Destination)": {"value": dst_distance, "unit": "mm"},
                "Rinse Volume": {"value": rinse_volume, "unit": "mL"},
                "Rinse Station No.": {"value": rinse_stn, "unit": None},
                "Airgap Volume": {"value": airgap, "unit": "mL"},
                "Post-Airgap Volume": {"value": post_airgap, "unit": "mL"},
                "Airgap Destination": {"value": airgap_dst, "unit": None},
                "Extra Volume": {"value": extra_volume, "unit": "mL"},
                "Extra Volume Destination": {"value": extra_dst, "unit": None},
                "Equilib. Time (Source)": {"value": equib_src, "unit": "s"},
                "Equilib. Time (Destination)": {"value": equib_dst, "unit": "s"},
                "Mult. Aspiration Allowed": {"value": int(multiple_asp), "unit": None}
            }
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
        """
        DEPRECATED! For injecting to the HPLC, use either transfer_liquid() directly, or refer to the routines sub-package.
                    Syntax / argument naming is different from transfer_liquid()

        Injects liquid to the specified HPLC injection ports. 

        Args:
            source: Source zone for the injection
            destination: Destination zone for the injection
            volume: Volume to inject [mL]
            src_flow: Draw speed at the source [mL/min]
            src_bu: Needle bottom-up distance at the source [mm]
            dst_flow: Dispense speed at the destination [mL/min]
            dst_bu: Needle bottom-up distance at the destination [mm]
            rinse_volume: Needle rinsing volume after action [mL]
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
            auto_dispense: bool = False,
            rd_speed: float = 30,
            rd_acc: float = 20,
            rd_amp: float = 100,
            fd_amount: float = 1,
            fd_speed: float = 30,
            fd_acc: float = 20,
            fd_amp: float = 40,
            fd_num: float = 360
    ) -> List[float]:
        """
        Executes a solid transfer from the source to the target destination.
        Uses the 'Transfer Gravimetrically' method in AutoSuite. 

        Args:
            source: Source zone for the solid transfer. 
            destination: Destination zone for the solid transfer. 
            weight: Mass to dispense [mg]
            height: Dispense height relative to vial top [mm]
            chunk: Rough dispensing chunk size [mg]
            equilib: Equilibration time for the balance [s]
            auto_dispense: True if the auto dispense feature of AutoSuite should be used.
            rd_speed: Rough dispensing rotation speed [rpm]
            rd_acc: Rough dispensing acceleration [s^-2]
            rd_amp: Rough dispensing rotation amplitute [%]
            fd_amount: Mass to be fine-dosed at the end of the dispense [mg]
            fd_speed: Fine dispensing rotation speed [rpm]
            fd_acc: Fine dispensing acceleration [s^-2]
            fd_amp: Fine dispensing rotation amplitute [%]
            fd_num: Fine dispensing angle [Deg]

        Returns:
            List[float]: Measured dispense weights [mg] 
        """
        # Get different data types into uniform WellGroup data type
        source: WellGroup = WellGroup(source, well_configuration=self.wells, logger=self.logger)
        destination: WellGroup = WellGroup(destination, well_configuration=self.wells, logger=self.logger)

        # Update well states and information
        source.remove_solid(quantity=weight)
        destination.add_solid(quantity=0)

        self.chemspeed.execute(
            "transfer_solid",
            **{
                "Source Zone": {"value": str(source), "unit": None},
                "Destination Zone": {"value": str(destination), "unit": None},
                "Mass": {"value": weight, "unit": "mg"},
                "Dispensing Height": {"value": height, "unit": "mm"},
                "Chunk Size": {"value": chunk, "unit": "mg"},
                "Equilibration Time": {"value": equilib, "unit": "s"},
                "Rough Dispensing Speed": {"value": rd_speed, "unit": "rpm"},  # TODO: Double-Check Units
                "Rough Dispensing Acceleration": {"value": rd_acc, "unit": "deg s^-2"},
                "Rough Dispensing Amplitude": {"value": rd_amp, "unit": None},
                "Fine Dispensing Amount": {"value": fd_amount, "unit": "mg"},
                "Fine Dispensing Speed": {"value": fd_speed, "unit": "rpm"},  # TODO: Double-Check Units
                "Fine Dispensing Acceleration": {"value": fd_acc, "unit": "deg s^-2"},
                "Fine Dispensing Amplitude": {"value": fd_amp, "unit": None},
                "Fine Dispensing Angle": {"value": fd_num, "unit": "°"},
                "Auto Dispense Activated": {"value": int(auto_dispense), "unit": None}
            }
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
                                  "can therefore not be executed via the Python controller at the current stage.")

        # Get different data types into uniform WellGroup data type
        source: WellGroup = WellGroup(source, well_configuration=self.wells, logger=self.logger)
        destination: WellGroup = WellGroup(destination, well_configuration=self.wells, logger=self.logger)

        # Update well states and information
        source.remove_solid(quantity=weight)
        destination.add_solid(quantity=0)

        self.chemspeed.execute(
            "transfer_solid_swile",
            **{
                "Source Zone": {"value": str(source), "unit": None},
                "Destination Zone": {"value": str(destination), "unit": None},
                "Mass": {"value": weight, "unit": "mg"},
                "Dispensing Height": {"value": height, "unit": "mm"},
                "Chunk Size": {"value": chunk, "unit": "mg"},
                "Equilibration Time": {"value": equilib, "unit": "s"},
                "Dipping Depth": {"value": depth, "unit": "mm"},
                "Pickup Volume": {"value": pickup, "unit": "µL"},
                "Rough Dispensing Step Size": {"value": rd_step, "unit": "µL"},
                "Fine Dispensing Step Size": {"value": fd_step, "unit": "µL"},
                "Shake Time": {"value": shake_time, "unit": "s"},
                "Shake Angle": {"value": shake_angle, "unit": "s"}
            }
        )

    def set_drawer(
            self,
            zone: Zone,
            state: str,
            environment: str = 'none'
    ):
        """
        Sets the drawer positions of the ISYNTH.
        Uses the 'Set Drawer Valve' method in AutoSuite. 

        Args:
            zone: Zone for setting the drawer state.
            state: Drawer state (open, close)
            environment: Environment state to set the zone (inert, vacuum, none)
        """
        zone = WellGroup(zone, well_configuration=self.wells, logger=self.logger)
        zone.set_parameter("drawer", state)
        zone.set_parameter("environment", environment)

        self.chemspeed.execute(
            "set_drawer",
            **{
                "Zone": {"value": str(zone), "unit": None},
                "Target State": {"value": state, "unit": None},
                "Environment": {"value": environment, "unit": None}
            }
        )

    @deprecated(deprecated_in="chemspyd-1.0", removed_in="chemspyd-2.0",
                details="ISYNTH-specific methods will be deprecated. Use set_reflux instead.")
    def set_isynth_reflux(
            self,
            state: str,
            temperature: float = 15
    ) -> None:
        """
        DEPRECATED: Use set_reflux with zone specification instead. 

        Sets the reflux state and temperature for the ISYNTH.

        Args:
            state: State of the cryostat (on, off)
            temperature: Temperature to set the condensor to [C]
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
        Uses the 'Reflux' method in AutoSuite. 

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
            **{
                "Zone": {"value": reflux_zone.get_element_string(), "unit": None},
                "Target State": {"value": state, "unit": None},
                "Chiller Temperature": {"value": temperature, "unit": "°C"}
            }
        )

    @deprecated(deprecated_in="chemspyd-1.0", removed_in="chemspyd-2.0",
                details="ISYNTH-specific methods will be deprecated. Use set_temperature instead.")
    def set_isynth_temperature(
            self,
            state: str,
            temperature: float = 15,
            ramp: float = 0
    ) -> None:
        """
        DEPRECATED: Use set_temperature with zone specification instead. 

        Sets the heating temperature of the ISYNTH.

        Args:
            state: Cryostat state (on, off)
            temperature: Temperature to set the cryostat to [C]
            ramp: Ramping speed for the temperature [C/min]
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
        Uses the 'Heat / Cool' method from AutoSuite.

        Args:
            temp_zone: Zone to be heated / cooled (ISYNTH, RACK_HS)
            state: Cryostat state (on, off)
            temperature: Temperature to set the cryostat to [C]
            ramp: Ramping speed for the temperature [C/min]
        """
        temp_zone = WellGroup(temp_zone, self.wells, logger=self.logger)
        temp_zone.set_parameter("thermostat", state)
        temp_zone.set_parameter("thermostat_temperature", temperature)
        temp_zone.set_parameter("thermostat_ramp", ramp)

        self.chemspeed.execute(
            "set_temperature",
            **{
                "Zone": {"value": temp_zone.get_element_string(), "unit": None},
                "Target State": {"value": state, "unit": None},
                "Temperature": {"value": temperature, "unit": "°C"},
                "Ramp Speed": {"value": ramp, "unit": "°C/min"}
            }
        )

    @deprecated(deprecated_in="chemspyd-1.0", removed_in="chemspyd-2.0",
                details="ISYNTH-specific methods will be deprecated. Use set_stir instead.")
    def set_isynth_stir(
            self,
            state: str,
            rpm: float = 200
    ) -> None:
        """
        DEPRECATED! Use set_stir with zone specification instead. 

        Sets the ISYNTH stirring status and speed.

        Args:
            state (str): Vortex state (on, off)
            rpm (float): Vortex rotation speed [rpm]
        """
        self.set_stir("ISYNTH:1", state, rpm)

    def set_stir(
            self,
            stir_zone: Zone,
            state: str,
            rpm: float = 0
    ) -> None:
        """
        Sets the stirring on a specified zone.
        Uses the 'Stir' method in AutoSuite.

        Args:
            stir_zone: Zone to be stirred
            state: Stir state (on, off)
            rpm: Stir rotation speed [rpm]
        """
        stir_zone = WellGroup(stir_zone, self.wells, logger=self.logger)
        stir_zone.set_parameter("stir", state)
        stir_zone.set_parameter("stir_rate", rpm)

        self.unmount_all()

        self.chemspeed.execute(
            "set_stir",
            **{
                "Zone": {"value": stir_zone.get_element_string(), "unit": None},
                "Target State": {"value": state, "unit": None},
                "Stir Rate": {"value": rpm, "unit": "rpm"}
            }
        )

    @deprecated(deprecated_in="chemspyd-1.0", removed_in="chemspyd-2.0",
                details="ISYNTH-specific methods will be deprecated. Use set_vacuum instead.")
    def set_isynth_vacuum(
            self,
            state: str,
            vacuum: float = 1000
    ) -> None:
        """
        DEPRECATED: Use set_vacuum with zone specification instead. 
        
        Sets the vacuum pressure and status on the ISYNTH. 

        Args:
            state: Vacuum pump state (on, off)
            vacuum: Vacuum pressure level [mbar]
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
        Uses the 'Set Vacuum' method in AutoSuite.

        Args:
            vac_zone: Zone to be set under vacuum
            state: Vacuum pump state state (on, off)
            vacuum: Pressure to set the vacuum pump to [mbar].
        """
        vac_zone = WellGroup(vac_zone, self.wells, logger=self.logger)
        vac_zone.set_parameter("vacuum_pump", state)
        vac_zone.set_parameter("vacuum_pump_pressure", vacuum)

        self.chemspeed.execute(
            "set_vacuum",
            **{
                "Zone": {"value": vac_zone.get_element_string(), "unit": None},
                "Target State": {"value": state, "unit": None},
                "Pressure": {"value": vacuum, "unit": "mbar"}
            }
        )

    @deprecated(deprecated_in="chemspyd-1.0", removed_in="chemspyd-2.0",
                details="ISYNTH-specific methods will be deprecated. Use operation-specific methods instead.")
    def set_isynth(
            self,
            **kwargs: Optional[Union[str, float]]
    ) -> None:
        """
        DEPRECATED: Use the set_vacuum, set_stir, set_temperature, set_reflux methods with zone specification instead. 
        
        Setting ISYNTH values. The following values can be [None, str, float]. If set at None, no change to current state.
        If "off" then turns off. If set to a value, then the system will turn on and set to that value.
        You have to specify the values to be set. For example, set_isynth(reflux=15) not set_isynth(15).

        Args:
            reflux: vacuum pressure level [mbar]
            temperature: vacuum pressure level [C]
            stir: vacuum pressure level [rpm]
            vacuum: vacuum pressure level [mbar]
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
            source: Source zone for vial for transfer
            destination: Zone for vial destination
            gripping_force: Gripping force for picking up the vials [N]
            gripping_depth: Gripping depth for the distance (down) to picking it up [mm]
            push_in: False if the vial should be dropped into the position (for the last mm).
            grip_inside: True if the vial should be gripped from the inside of the neck.
        """
        source = WellGroup(source, well_configuration=self.wells, logger=self.logger)
        destination = WellGroup(destination, well_configuration=self.wells, logger=self.logger)

        self.chemspeed.execute(
            "vial_transport",
            **{
                "Source Zone": {"value": str(source), "unit": None},
                "Destination Zone": {"value": str(destination), "unit": None},
                "Gripping Force": {"value": gripping_force, "unit": "N"},
                "Gripping Depth": {"value": gripping_depth, "unit": "mm"},
                "Push Vial In": {"value": int(push_in), "unit": None},
                "Grip Vial from Inside": {"value": int(grip_inside), "unit": None}
            }
        )

    def set_zone_state(
            self,
            zone: Zone,
            state: bool = True
    ) -> None:
        """
        Method to re-set the 'enabled' state of a zone on AutoSuite. Certain operations may turn off the availability of a zone.
        
        Args:
            zone: Zone to change the state
            state: Target status: Enable (True) or Disable (False)
        """
        zone = WellGroup(zone, well_configuration=self.wells, logger=self.logger)

        self.chemspeed.execute(
            "set_zone_state",
            **{
                "Zone": {"value": zone, "unit": None},
                "Target State": {"value": int(state), "unit": None}
            }
        )

    def measure_level(
            self,
            zone: Zone
    ) -> List[float]:
        """
        Measure the material level in a certain well.

        Args:
            Zone: Zones to measure the volume in.

        Returns:
            List[float]: List of determined quantities per well.     
        """
        zone = WellGroup(zone, well_configuration=self.wells, logger=self.logger)

        self.chemspeed.execute(
            "measure_level",
            **{
                "Zone": {"value": str(zone), "unit": None}
            }
        )

        return [float(level) for level in self.chemspeed.return_data]

    def unmount_all(self):
        """
        Unmount all tools from the arm. 
        """
        self.chemspeed.execute('unmount_all')

    def stop_manager(self):
        """
        Stops the manager safely from the python controller.
        """
        self.chemspeed.execute('stop_manager')

    def read_status(
            self,
            key: Optional[str] = None
    ) -> Union[Dict[str, float], float]:
        """
        Reads the Chemspeed status while the instrument is idle.

        Args:
            key: Status to read (from the specified keys in self.status_keys)

        Returns:
            values: Single float value of the specified key, dictionary of all keys and values if no key is specified.
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
        Waits for a set duration.
        Uses the 'Wait' method in AutoSuite.

        Args:
            duration: Duration of wait (in seconds)
        """
        self.chemspeed.execute(
            "wait",
            **{
                "Time": {"value": duration, "unit": "s"}
            }
        )
