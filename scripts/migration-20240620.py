# This is a migration script used to migrate the data from the previous that we use to this format.
# To run the migration script: `poetry run python3 -m scripts.migration` from the root folder.

from json import load
from os import path
from pathlib import Path

from src.database import Database
from src.schema import BaseSchema, DatabaseEntry


class Experience(BaseSchema):
    xp_goal: int
    xp_today: int


class SessionInformation(BaseSchema):
    number_of_sessions: int
    session_time: int


class Progression(BaseSchema):
    experience: Experience
    session_information: SessionInformation


class StreakInformation(BaseSchema):
    site_streak: int


class OldDatabaseEntry(BaseSchema):
    date: str
    progression: Progression
    streak_information: StreakInformation
    time: str


def main():
    # Define constants.
    file_path = Path(__file__).parent.absolute()
    old_filename = "duolingo-progress.json"
    new_progression_database_filename = "duolingo-progress-new.json"
    new_statistics_database_filename = "statistics.json"

    # Get data from the real database.
    old_database_path = path.join(file_path, "..", "data", old_filename)
    with open(old_database_path, "r") as file:
        raw_old_database = load(file)

    # Map the data to the old data structure.
    parsed_old_database = [OldDatabaseEntry(**data) for data in raw_old_database]

    # Migrate to the new data structure.
    new_progression_database = {
        data.date: (
            DatabaseEntry(
                date=data.date,
                xp_today=data.progression.experience.xp_today,
                number_of_sessions=data.progression.session_information.number_of_sessions,
                session_time=data.progression.session_information.session_time,
                streak=data.streak_information.site_streak,
            )
        )
        for data in parsed_old_database
    }
    new_statistics_database = {data.date: data.time for data in parsed_old_database}

    # Prepare the databases.
    progression_database = Database(
        filename=path.join(file_path, "..", "data", new_progression_database_filename)
    )
    statistics_database = Database(
        filename=path.join(file_path, "..", "data", new_statistics_database_filename)
    )

    # Map the data so it can be accepted by the database.
    progression_database.set(
        {key: value.model_dump() for key, value in new_progression_database.items()}
    )
    statistics_database.set(new_statistics_database)

    # Print success screen.
    print("Migration script has been successfully run!")


if __name__ == "__main__":
    main()
