from json import dump, load
from pathlib import Path

import pytest
from pydantic import JsonValue

from src.database import Database


@pytest.fixture
def sample_data() -> JsonValue:
    return {"key1": "value1", "key2": 42, "nested": {"key3": [1, 2, 3]}}


@pytest.fixture
def temp_db_file(tmp_path: Path) -> Path:
    return tmp_path / "test_db.json"


def test_set_creates_file_with_correct_content(
    temp_db_file: Path, sample_data: JsonValue
):
    db = Database(filename=str(temp_db_file))
    db.set(sample_data)

    assert temp_db_file.exists(), "Database file was not created"
    with open(temp_db_file, "r", encoding="UTF-8") as file:
        data = load(file)
        assert data == sample_data, "Data in the file does not match the expected data"


def test_get_retrieves_correct_content(temp_db_file: Path, sample_data: JsonValue):
    with open(temp_db_file, "w", encoding="UTF-8") as file:
        dump(sample_data, file, ensure_ascii=False, indent=2, sort_keys=True)

    db = Database(filename=str(temp_db_file))
    data = db.get()
    assert data == sample_data, "Data in the file does not match the expected data"


def test_set_overwrites_existing_content(temp_db_file: Path, sample_data: JsonValue):
    initial_data = {"initial_key": "initial_value"}
    with open(temp_db_file, "w", encoding="UTF-8") as file:
        dump(initial_data, file, ensure_ascii=False, indent=2, sort_keys=True)

    db = Database(filename=str(temp_db_file))
    db.set(sample_data)

    with open(temp_db_file, "r", encoding="UTF-8") as file:
        data = load(file)
        assert data == sample_data, "Data in the file does not match the expected data"
