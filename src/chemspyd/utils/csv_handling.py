from pathlib import Path
from typing import List


def read_csv(file_name: Path, single_line: bool = False, delimiter: str = ",") -> List:
    """
    Reads in a csv file and returns each line as a list of entries.

    Args:
        file_name: Path to the csv file
        single_line: True if only a single line from the file should be read. Else returns a list of lists.
        delimiter: CSV column delimiter.

    Returns:
         List or List[List]: Each line as a list of entries.
    """
    with open(file_name, "r") as input_file:
        lines: list = input_file.readlines()

    if single_line:
        return lines[0].split(sep=delimiter)
    else:
        return [line.split(sep=delimiter) for line in lines]


def write_csv(lines: list, file_name: Path, single_line: bool = False, delimiter: str = ",") -> None:
    """
    Writes a list of rows into a csv file.

    Args:
        lines: List[list] of rows (each row as a list). If single_line is given, lines is a simple list.
        file_name: Path to the csv file
        single_line: True if only a single line should be written to the file.
        delimiter: CSV column delimiter.
    """
    if single_line:
        lines = [lines]

    with open(file_name, "w") as output_file:
        for line in lines:
            output_file.write(f"{delimiter.join(line)}\n")
