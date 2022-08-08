from typing import Union, List
from pathlib import Path
from logging import Logger
import time

from .utils import read_csv, write_csv


class ChemspeedExecutor(object):
    """

    """
    def __init__(
            self,
            cmd_folder: Union[str, Path],
            logger: Logger,
            simulation: bool = False,
    ):
        """

        Args:
            cmd_folder: Path to the folder containing the csv files for communicating with the instrument.
            logger: logging.Logger object
            simulation: True in order to run the Python controller (not Autosuite!) in simulation mode.
                        Will only print execution statements then (without sending any commands to the instrument).
        """
        self.logger: Logger = logger

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

    #######################################
    # Execution of Commands to AutoSuite  #
    #######################################

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
        while self.blocked:
            time.sleep(0.1)
        write_csv([[1, command], [args_line, "end"]], file_name=self.command_file)

        # stdout & logging
        self.logger.info(exec_message, extra={"continue_line": True})

        # wait until no idle to confirm that the command was executed
        while self.idle:
            time.sleep(0.1)
        self.logger.debug("-> started", extra={"format": False, "continue_line": True})

        # self block, optional, or change to error detection
        while self.blocked:
            time.sleep(0.1)
        self.logger.debug("-> completed", extra={"format": False})
