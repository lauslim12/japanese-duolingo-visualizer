"""Main runner, expected to be run as a command line program."""

from sys import exit
from os import environ, path
from traceback import format_exc


from src.duolingo import (
    DatabaseEntry,
    Duolingo,
    summary_to_progression,
    sync_database_with_summaries,
    user_data_to_streak_information,
    progression_to_database_entry,
)
from src.store import Store


def main() -> None:
    """
    What we want:
    - Validate our credentials.
    - Login to Duolingo with our credentials in our environment.
    - Fetch all necessary data.
    - Store data in a JSON file with 2 indentation and sorted keys.
    - Outside of this script, please commit to GitHub (either via GitHub Actions or a standalone server cronjob).
    """
    try:
        # If there's no username nor password or JWT.
        if not environ.get("DUOLINGO_USERNAME") and (
            not environ.get("DUOLINGO_PASSWORD") or not environ.get("DUOLINGO_JWT")
        ):
            raise Duolingo.LoginException(
                "Japanese Duolingo Visualizer script requires your username, and either your password or JWT."
            )

        # Duolingo API client initialization.
        lingo = Duolingo(
            username=environ.get("DUOLINGO_USERNAME"),
            password=environ.get("DUOLINGO_PASSWORD"),
            jwt=environ.get("DUOLINGO_JWT"),
            daily_experience_progress={},
            user_data={},
        )

        # Log in to the API client.
        lingo.login()

        # Print a message.
        print(
            "[JDV] Japanese Duolingo Visualizer script has successfully logged in to your account."
        )

        # Print a message with the login type.
        print(
            f"[JDV] Japanese Duolingo Visualizer script logged in to your account with {lingo.login_method} method."
        )

        # Fetch the data.
        lingo.fetch_data()

        # Shape our data. Indice `0` will always be there because it's Duolingo last active day data.
        user_data = lingo.get_user_data()
        summaries = lingo.get_summaries()
        progression = summary_to_progression(summaries[0])
        streak_information = user_data_to_streak_information(user_data)
        entry = progression_to_database_entry(progression, streak_information)

        # Print a message.
        print(
            "[JDV] Japanese Duolingo Visualizer script has successfully fetched the necessary information!"
        )

        # Prepare a file to take and store our data from/to.
        store = Store(path.join("data", "duolingo-progress.json"), [])
        store.get_from_json_file()

        # Append the latest entry to the current database, and then sync it with the existing summaries.
        store.content.append(entry.model_dump())

        # Synchronize our data.
        database = [DatabaseEntry(**data) for data in store.content]
        synced_database, changed = sync_database_with_summaries(summaries, database)
        if changed:
            print(
                "[JDV] Japanese Duolingo Visualizer script has synchronized your data."
            )

        # Stores our data to a file.
        store.content = [data.model_dump() for data in synced_database]
        store.store_to_json_file()

        # Print success message.
        print(
            "[JDV] Japanese Duolingo Visualizer script is successful! Please check your specified `filename` path to see your newly updated data."
        )
        exit(0)
    except (
        Duolingo.BreakingAPIChange,
        Duolingo.CaptchaException,
        Duolingo.LoginException,
        Duolingo.NotFoundException,
        Duolingo.UnauthorizedException,
    ) as error:
        print(f"[JDV] {error.__class__.__name__}: {error}")
        exit(1)
    except Exception as error:
        print(f"[JDV] Unexpected Exception: {error.__class__.__name__}: {error}")
        print(format_exc())
        exit(1)
    finally:
        print("[JDV] Japanese Duolingo Visualizer script has finished running.")


if __name__ == "__main__":
    main()
