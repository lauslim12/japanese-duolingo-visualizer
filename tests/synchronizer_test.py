from datetime import datetime

import pytest

from src.schema import DatabaseEntry, Summary
from src.synchronizer import (
    check_database_change,
    find_start_and_end_dates,
    generate_dates_between,
    sync_database_with_summaries,
)


def _convert_yyyy_mm_dd_to_date(date: str) -> int:
    return int(datetime.strptime(date, "%Y/%m/%d").timestamp())


@pytest.fixture
def empty_summaries() -> list[Summary]:
    return []


@pytest.fixture
def sample_summaries() -> list[Summary]:
    return [
        Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/02")),
        Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/03")),
    ]


@pytest.fixture
def excess_summaries() -> list[Summary]:
    return [
        Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/01")),
        Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/02")),
        Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/03")),
        Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/04")),
    ]


@pytest.fixture
def sample_database() -> list[DatabaseEntry]:
    """This database has an out of synchronization streak for testability."""
    return [
        DatabaseEntry.create_default("2024/06/01", 0),
        DatabaseEntry.create_default("2024/06/02", 0),
        DatabaseEntry.create_default("2024/06/03", 0),
    ]


def test_sync_empty_summaries(sample_database, empty_summaries):
    expected_database_with_streak = [
        DatabaseEntry.create_default("2024/06/01", 0),
        DatabaseEntry.create_default("2024/06/02", 0),
        DatabaseEntry.create_default("2024/06/03", 0),
    ]

    actual_database = sync_database_with_summaries(sample_database, empty_summaries)
    assert actual_database == expected_database_with_streak


def test_sync_with_summaries(sample_database, sample_summaries):
    expected_database_with_streak = [
        DatabaseEntry.create_default("2024/06/01", 0),
        DatabaseEntry.create_default("2024/06/02", 1),
        DatabaseEntry.create_default("2024/06/03", 2),
    ]

    actual_database = sync_database_with_summaries(sample_database, sample_summaries)
    assert actual_database == expected_database_with_streak


def test_sync_with_missing_dates_in_summaries(sample_database):
    summaries = [Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/01"))]
    expected_database = [
        DatabaseEntry.create_default("2024/06/01", 1),
        DatabaseEntry.create_default("2024/06/02", 0),
        DatabaseEntry.create_default("2024/06/03", 0),
    ]

    actual_database = sync_database_with_summaries(sample_database, summaries)
    assert actual_database == expected_database


def test_sync_with_excess_summaries(sample_database):
    summaries = [
        Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/01")),
        Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/02")),
        Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/03")),
        Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/04")),
        Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/05")),
        Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/06")),
    ]
    expected_database = [
        DatabaseEntry.create_default("2024/06/01", 1),
        DatabaseEntry.create_default("2024/06/02", 2),
        DatabaseEntry.create_default("2024/06/03", 3),
        DatabaseEntry.create_default("2024/06/04", 4),
        DatabaseEntry.create_default("2024/06/05", 5),
        DatabaseEntry.create_default("2024/06/06", 6),
    ]

    actual_database = sync_database_with_summaries(sample_database, summaries)
    assert actual_database == expected_database


def test_sync_with_continuous_summaries(sample_database):
    summaries = [
        Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/01")),
        Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/02")),
        Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/03")),
    ]
    expected_database = [
        DatabaseEntry.create_default("2024/06/01", 1),
        DatabaseEntry.create_default("2024/06/02", 2),
        DatabaseEntry.create_default("2024/06/03", 3),
    ]

    actual_database = sync_database_with_summaries(sample_database, summaries)
    assert actual_database == expected_database


def test_sync_with_gaps_in_summaries():
    summaries = [
        Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/01")),
        Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/02")),
        Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/04")),
        Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/06")),
        Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/07")),
    ]
    database = [
        DatabaseEntry.create_default("2024/06/01", 1),
        DatabaseEntry.create_default("2024/06/02", 2),
        DatabaseEntry.create_default("2024/06/03", 3),
        DatabaseEntry.create_default("2024/06/04", 4),
        DatabaseEntry.create_default("2024/06/05", 5),
        DatabaseEntry.create_default("2024/06/06", 6),
        DatabaseEntry.create_default("2024/06/07", 7),
    ]
    expected_database = [
        DatabaseEntry.create_default("2024/06/01", 1),
        DatabaseEntry.create_default("2024/06/02", 2),
        DatabaseEntry.create_default("2024/06/03", 0),
        DatabaseEntry.create_default("2024/06/04", 1),
        DatabaseEntry.create_default("2024/06/05", 0),
        DatabaseEntry.create_default("2024/06/06", 1),
        DatabaseEntry.create_default("2024/06/07", 2),
    ]

    actual_database = sync_database_with_summaries(database, summaries)
    assert actual_database == expected_database


@pytest.mark.parametrize(
    "start_date, end_date, expected_dates",
    [
        (
            "2024/06/01",
            "2024/06/04",
            ["2024/06/01", "2024/06/02", "2024/06/03", "2024/06/04"],
        ),
        ("2024/06/01", "2024/06/01", ["2024/06/01"]),
        ("2024/06/01", "2024/05/31", []),
    ],
)
def test_generate_dates_between(start_date, end_date, expected_dates):
    assert generate_dates_between(start_date, end_date) == expected_dates


@pytest.mark.parametrize(
    "database, summaries, expected_start_date, expected_end_date",
    [
        (
            [
                DatabaseEntry.create_default("2024/06/01", 1),
                DatabaseEntry.create_default("2024/06/02", 2),
            ],
            [
                Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/03")),
                Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/04")),
            ],
            "2024/06/01",
            "2024/06/04",
        ),
        (
            [
                DatabaseEntry.create_default("2024/06/01", 1),
                DatabaseEntry.create_default("2024/06/03", 1),
            ],
            [],
            "2024/06/01",
            "2024/06/03",
        ),
        (
            [],
            [
                Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/01")),
                Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/02")),
                Summary.create_default(_convert_yyyy_mm_dd_to_date("2024/06/05")),
            ],
            "2024/06/01",
            "2024/06/05",
        ),
    ],
)
def test_find_start_and_end_dates(
    database, summaries, expected_start_date, expected_end_date
):
    start_date, end_date = find_start_and_end_dates(database, summaries)
    assert start_date == expected_start_date
    assert end_date == expected_end_date


def test_find_start_and_end_dates_if_empty():
    with pytest.raises(ValueError):
        find_start_and_end_dates([], [])


@pytest.mark.parametrize(
    "old_database, new_database, expected",
    [
        (
            [
                DatabaseEntry.create_default("2024/06/01", 1),
                DatabaseEntry.create_default("2024/06/02", 2),
            ],
            [
                DatabaseEntry.create_default("2024/06/01", 1),
                DatabaseEntry.create_default("2024/06/02", 2),
            ],
            False,
        ),
        (
            [
                DatabaseEntry.create_default("2024/06/01", 1),
                DatabaseEntry.create_default("2024/06/02", 2),
            ],
            [
                DatabaseEntry.create_default("2024/06/01", 1),
                DatabaseEntry.create_default("2024/06/02", 2),
                DatabaseEntry.create_default("2024/06/03", 3),
            ],
            True,
        ),
        (
            [
                DatabaseEntry.create_default("2024/06/01", 1),
                DatabaseEntry.create_default("2024/06/02", 2),
                DatabaseEntry.create_default("2024/06/03", 3),
            ],
            [
                DatabaseEntry.create_default("2024/06/01", 1),
                DatabaseEntry.create_default("2024/06/02", 2),
            ],
            True,
        ),
    ],
)
def test_check_database_change(old_database, new_database, expected):
    assert check_database_change(old_database, new_database) == expected
