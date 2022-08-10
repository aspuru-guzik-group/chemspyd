#!/usr/bin/python
# -*- coding: UTF-8 -*-

from typing import Union, List
from pathlib import Path
from logging import Logger
import time

from .utils import read_csv, write_csv


class ChemspeedExecutor(object):
    """
    Executor class for communication with the Manager, executed by the AutoSuiteExecutor.

    Communicates by reading and writing the following four files:
        - command.csv   (Commands sent to the instrument)
        - response.csv  (Response by the instrument - idle / busy information)
        - return.csv    (Values and data returned from functions in the Manager)
        - status.csv    (Instrument status written by the Manager)
    """

    def __init__(
            self,
            cmd_folder: Union[str, Path],
            logger: Logger,
            verbosity: int = 3,
            simulation: bool = False,
    ):
        """
        Instantiates the ChemspeedExecutor.

        Args:
            cmd_folder: Path to the folder containing the csv files for communicating with the instrument.
            logger: logging.Logger object
            verbosity: Verbosity level (between 0 and 3; 0 -> no output, 3 -> very verbose output)
            simulation: True in order to run the Python controller (not Autosuite!) in simulation mode.
                        Will only print execution statements then (without sending any commands to the instrument).
        """
        self.logger: Logger = logger
        self.verbosity: int = verbosity

        self.command_file: Path = Path(cmd_folder) / "command.csv"
        self.response_file: Path = Path(cmd_folder) / "response.csv"
        self.status_file: Path = Path(cmd_folder) / "status.csv"
        self.return_file: Path = Path(cmd_folder) / "return.csv"

        self.simulation: bool = simulation

    ########################################################
    # File-Level Communication with the AutoSuite Executor #
    ########################################################

    @property
    def idle(self) -> bool:
        """
        Checks for the instrument to be idle.

        Returns:
            bool: True if the instrument is idle, else False.
        """
        rsp_readout: list = read_csv(self.response_file, single_line=True)
        return rsp_readout[0] == "1"

    @property
    def newcmd(self) -> bool:
        """
        Checks if the instrument has received a new command.

        Returns:
            bool: True if it has received a new command, else False.
        """
        cmd_readout: list = read_csv(self.command_file, single_line=True)
        return cmd_readout[0] == "1"

    @property
    def blocked(self) -> bool:
        """
        Checks if the instrument is blocked, i.e.
            - not idle
            - has received a new command

        Returns:
            bool: True if the instrument is blocked, else False.
        """
        return not self.idle or self.newcmd

    @property
    def return_data(self) -> List[str]:
        """
        Reads in the return data written by AutoSuite Executor.

        Returns:
            list: List of all return values (removing the last element which is "end" by definition).
        """
        return read_csv(self.return_file, single_line=True)[:-1]

    @property
    def status(self) -> List[str]:
        """
        Reads in the status data sent by AutoSuite Executor.

        Returns:
            list: List of all status values (removing the last element which is "end" by definition).
        """
        return read_csv(self.status_file, single_line=True)[:-1]

    ###########################################################
    # Execution of Commands to send to the AutoSuiteExecutor  #
    ###########################################################

    def execute(self, command: str, **kwargs) -> None:
        """
        Main method to execute a given operation.
        Writes the command into the command.csv file, including the command name and all required arguments.

        Args:
            command (str): The command name to be received in Chemspeed.
            **kwargs: Dictionary of keyword arguments for the command.
                      Keys are arbitrary and are just used for logging.
        """
        args_line = ','.join([str(kwargs[kwarg]["value"]) for kwarg in kwargs])

        # skip everything if simulation
        if self.simulation:
            self._log_command_details(command, kwargs)
            return

        # send to file
        while self.blocked:
            time.sleep(0.1)

        write_csv([[1, command], [args_line, "end"]], file_name=self.command_file)
        self._log_command_details(command, kwargs)

        # wait until self.idle == False to confirm that the command was executed
        while self.idle:
            time.sleep(0.1)
        self.logger.debug("    Execution Started: ✓  ", extra={"continue_line": True})

        # self block, optional, or change to error detection
        while self.blocked:
            time.sleep(0.1)
        self.logger.debug("Execution Completed: ✓", extra={"format": False})

    def _log_command_details(self, command: str, kwargs: dict) -> None:
        """
        Logs the details of the execution of a given command based on the verbosity level specified:
            0: ---
            1: Executing set_stir
            2: Executing set_stir(ISYNTH:1, on, 200)
            3: Executing set_stir
                   stir_zone: ISYNTH:1
                   state: on
                   stir_rate: 200

        Args:
            command: The command name to be sent to the AutoSuiteExecutor.
            kwargs: Keyword arguments for the command.
        """
        if self.verbosity == 1:
            self.logger.info(f"Executing {command}.")

        elif self.verbosity == 2:
            self.logger.info(f"Executing {command} ({', '.join([str(kwargs[kwarg]['value']) for kwarg in kwargs])})")

        elif self.verbosity >= 3:
            self.logger.info(f"Executing {command}.")
            for arg_name, arg_value in zip(kwargs, kwargs.values()):
                unit = arg_value["unit"] if arg_value["unit"] is not None else ""
                self.logger.info(f"{' '*24}{arg_name} = {arg_value['value']} {unit}", extra={"format": False})
                # FIXME: Spacing is hard-coded currently, should be rather inferred from the logger.
