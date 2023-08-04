"""Store is a class to handle file input/output for this tool."""

from dataclasses import dataclass
from json import JSONDecodeError, dump, load

from .duolingo import DatabaseEntry


@dataclass
class Store:
    """
    Store handles all file input/output and processing steps properly.
    """

    class StoreException(Exception):
        """Exception that will be raised if unwanted things happen during the usage of this class."""

    filename: str
    content: list[DatabaseEntry]

    def get_from_json_file(self) -> None:
        """
        Attempts to read from `filename` to parse the JSON that is available in that file. If
        the program caught an environment error (parent of `IOError`, `OSError`, and `WindowsError` if
        applicable), it will raise an exception and will not continue. If failed to parse the JSON,
        then `content` will be set to an empty array `[]`.
        """
        try:
            with open(self.filename, "r", encoding="UTF-8") as file:
                try:
                    self.content = load(file)
                except JSONDecodeError as error:
                    self.content = []
        except EnvironmentError as error:
            raise self.StoreException(f"Environment error: {error}.")

    def store_to_json_file(self) -> None:
        """
        Stores `content` to `filename`.
        """
        with open(self.filename, "w", encoding="UTF-8") as file:
            dump(self.content, file, ensure_ascii=False, indent=2, sort_keys=True)
