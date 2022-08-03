from typing import Union, Any
from pathlib import Path
import json


def load_json(file: Union[str, Path]) -> Any:
    """
    Loads a json file and returns the loaded object.

    Args:
        file: Path to the json file to be loaded.

    Returns:
        Any: object saved in the json file
    """
    with open(file, "r") as json_file:
        loaded_object: Any = json.load(json_file)

    return loaded_object


def save_json(object_to_save: Any, file: Union[str, Path]) -> None:
    """
    Saves an object as a json file.

    Args:
        object_to_save: Object to be saved (must be json-serializable).
        file: Path to the json file.
    """
    with open(file, "w") as json_file:
        json.dump(object_to_save, json_file)
