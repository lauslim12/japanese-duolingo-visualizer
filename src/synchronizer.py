from datetime import datetime, timedelta
from itertools import accumulate, count, takewhile

from src.schema import DatabaseEntry, Summary


def generate_dates_between(start_date_str: str, end_date_str: str) -> list[str]:
    start_date = datetime.strptime(start_date_str, "%Y/%m/%d")
    end_date = datetime.strptime(end_date_str, "%Y/%m/%d")

    # Generator to yield dates from start to end, inclusive.
    date_generator = (start_date + timedelta(days=x) for x in count())

    # Collect dates until the end is reached.
    dates_between = takewhile(lambda date: date <= end_date, date_generator)

    # Convert the date to string format and return it.
    return [date.strftime("%Y/%m/%d") for date in dates_between]


def find_start_and_end_dates(
    database: list[DatabaseEntry], summaries: list[Summary]
) -> tuple[str, str]:
    # Check for invalid inputs at first.
    if not database and not summaries:
        raise ValueError(
            "Both database and summaries are empty. Cannot determine start and end dates."
        )

    if not database:
        summary_dates = [
            datetime.fromtimestamp(summary.date).strftime("%Y/%m/%d")
            for summary in summaries
        ]
        start_date, end_date = min(summary_dates), max(summary_dates)
        return start_date, end_date

    if not summaries:
        database_dates = [entry.date for entry in database]
        start_date, end_date = min(database_dates), max(database_dates)
        return start_date, end_date

    # If inputs are valid, cover both dates.
    database_dates = [entry.date for entry in database]
    summary_dates = [
        datetime.fromtimestamp(summary.date).strftime("%Y/%m/%d")
        for summary in summaries
    ]
    all_dates = database_dates + summary_dates
    start_date, end_date = min(all_dates), max(all_dates)

    return start_date, end_date


def check_database_change(old: list[DatabaseEntry], new: list[DatabaseEntry]) -> bool:
    if len(old) != len(new):
        return True

    old_set = {frozenset(DatabaseEntry.to_dict(entry).items()) for entry in old}
    new_set = {frozenset(DatabaseEntry.to_dict(entry).items()) for entry in new}

    return old_set != new_set


def sync_database_with_summaries(
    database: list[DatabaseEntry], summaries: list[Summary]
) -> list[DatabaseEntry]:
    # Create a dictionary of summaries keyed by date string.
    synchronized_record = {
        datetime.fromtimestamp(summary.date).strftime("%Y/%m/%d"): summary
        for summary in summaries
    }

    # Generate all the dates (inclusive) between the start and the end of
    # the combination of the database and the summary.
    start_date, end_date = find_start_and_end_dates(database, summaries)
    dates = generate_dates_between(start_date, end_date)

    # Calculate streaks declaratively to maintain cumulative streaks. If it cannot find
    # a date in the record, reset back to zero. At the end, `streaks` MUST have the same length
    # as the dates. Check the tests for more information regarding the supposed behavior of this algorithm.
    streaks = accumulate(
        (1 if date in synchronized_record else 0 for date in dates),
        lambda streak, exists: (streak + 1) if exists else 0,
    )

    # The streak will be synchronized by iterating through all of the dates and trying to find the equivalent
    # in summaries. If it doesn't exist, then it will set the data to a generic, default zero data. The
    # generator expression is used to accumulate the count of dates in the record. It will reset to
    # zero whenever `date` cannot be found in the dates.
    synchronized_database = [
        (
            DatabaseEntry.create(summary, date, streak)
            if (summary := synchronized_record.get(date)) is not None
            else DatabaseEntry.create_default(date, 0)
        )
        for date, streak in zip(dates, streaks)
    ]

    return synchronized_database
