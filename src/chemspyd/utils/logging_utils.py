from typing import Union
from pathlib import Path
import logging


class ConsoleStreamHandler(logging.Handler):
    """
    Stream Handler that allows for specifying different formatting of console output.
    Console output format can be defined by passing the extra keyword argument when creating the logRecord.
        - flexible inclusion of line breaks (no line break if extra={"continue_line": True})
        - flexible formatting of messages (no additional formatting if extra={"format": False})
    """
    def emit(self, record: logging.LogRecord) -> None:
        """
        Prints the logged message to the console.

        If the log record has the "continue_line" attribute, the line will be continued.
        Else terminates regularly (i.e. with a line break).

        Args:
            record: LogRecord of the message.
        """
        if hasattr(record, "format"):
            message: str = str(record.msg)
        else:
            message: str = self.format(record)
        terminate: str = " " if hasattr(record, "continue_line") else "\n"
        print(message, end=terminate, flush=True)


def get_logger(stdout: bool = True, logfile: Union[str, Path, None] = None):
    """
    Creates a logging.Logger object that handles logging for all ChemSpeed operations.

    ATTN:   Currently, all specifications (formatting, handlers etc) are hard-coded. Should this stay like that?
            Or should all logger specifications be defined in a json file (using logging.dictConfig)?

    Args:
        stdout: True if console output should be generated.
        logfile: Path to the logfile where events should be logged. If None, no logfile is written.

    Returns:
        logging.Logger: configured Logger instance
    """
    logger = logging.getLogger("ChemspeedLogger")
    logger.setLevel("DEBUG")

    formatter: logging.Formatter = logging.Formatter(
        fmt="%(asctime)s - %(message)s",
        datefmt="%y-%m-%d %H:%M:%S"
    )

    if logfile:
        logfile_handler: logging.Handler = logging.FileHandler(filename=logfile, encoding="utf-8")
        logfile_handler.setLevel("INFO")
        logfile_handler.setFormatter(formatter)
        logger.addHandler(logfile_handler)

    if stdout:
        stream_handler: logging.Handler = ConsoleStreamHandler("DEBUG")
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger
