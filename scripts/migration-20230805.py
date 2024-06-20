# This is a migration script used to migrate the data from the initial format that we use to the this format.
# To run the migration script: `poetry run python3 -m scripts.migration` from the root folder.

from json import dump, load
from os import path
from pathlib import Path

from pydantic import BaseModel

from src.duolingo import (
    DatabaseEntry,
    Experience,
    Progression,
    SessionInformation,
    StreakInformation,
)


class OldDatabaseEntry(BaseModel):
    date: str
    experience: Experience
    number_of_learned_words: int
    session_information: SessionInformation
    streak_information: StreakInformation
    time: str


def main():
    # 0. Define constants.
    file_path = Path(__file__).parent.absolute()
    old_filename = "duolingo-progress.json"
    new_filename = "duolingo-progress-new.json"

    # 1. Get data from the real database.
    old_database_path = path.join(file_path, "..", "data", old_filename)
    with open(old_database_path, "r") as file:
        raw_old_database = load(file)

    # 2. Map the data to the old data structure.
    parsed_old_database = [OldDatabaseEntry(**data) for data in raw_old_database]

    # 3. Migrate to the new data structure.
    new_database = [
        DatabaseEntry(
            date=data.date,
            progression=Progression(
                experience=data.experience,
                session_information=data.session_information,
            ),
            streak_information=StreakInformation(
                site_streak=data.streak_information.site_streak
            ),
            time=data.time,
        )
        for data in parsed_old_database
    ]

    # 4. Put the database to the specified path.
    new_database_path = path.join(file_path, "..", "data", new_filename)
    new_database_to_write = [data.model_dump() for data in new_database]
    with open(new_database_path, "w", encoding="UTF-8") as file:
        dump(new_database_to_write, file, ensure_ascii=False, indent=2, sort_keys=True)

    # 5. Print success screen.
    print("Migration script has been successfully run!")


if __name__ == "__main__":
    main()
