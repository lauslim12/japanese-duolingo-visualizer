"""Store is a class to handle file input/output for this tool."""

from dataclasses import dataclass
from json import JSONDecodeError, dump, load
from typing import Any


@dataclass
class Store:
    """
    Store handles all file input/output and processing steps properly.
    """

    class StoreException(Exception):
        """Exception that will be raised if unwanted things happen during the usage of this class."""

    data: dict[str, Any]
    filename: str
    json_content: list[dict[str, Any]]

    def get_from_json_file(self) -> None:
        """
        Attempts to read from `filename` to parse the JSON that is available in that file. If
        the program caught an environment error (parent of `IOError`, `OSError`, and `WindowsError` if
        applicable), it will raise an exception and will not continue. If failed to parse the JSON,
        then `json_content` will be set to an empty array `[]`.
        """
        try:
            with open(self.filename, "r", encoding="UTF-8") as file:
                try:
                    self.json_content = load(file)
                except JSONDecodeError as error:
                    self.json_content = []
        except EnvironmentError as error:
            raise self.StoreException(f"Environment error: {error}.")

    def store_to_json_file(self) -> None:
        """
        Stores `json_content` to `filename`. Before you do this, please do `process_json_data` first.
        If you're wondering why I code like this, it is because I want to conform to the Single Responsibility
        Principle. Sadly, this is not a pure function as it involves input/output.
        """
        with open(self.filename, "w", encoding="UTF-8") as file:
            dump(self.json_content, file, ensure_ascii=False, indent=2, sort_keys=True)

    def process_json_data(self) -> None:
        """
        Appends `json_content` with `data`.
        """
        self.json_content.append(self.data)
