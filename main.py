from os import environ, path
from traceback import format_exc

from pydantic import ValidationError

from src.api import (
    APIClient,
    CaptchaException,
    LoginException,
    NotFoundException,
    UnauthorizedException,
)
from src.database import Database
from src.schema import DatabaseEntry, Statistics, Summary, User
from src.synchronizer import check_database_change, sync_database_with_summaries


def log(message: str) -> None:
    print(f"[JDV] {message}")


def run() -> tuple[bool, bool]:
    # Initialize environment.
    base_api_url = "https://www.duolingo.com"
    username = environ["DUOLINGO_USERNAME"]
    credential, passwordless = (
        (credential, True)
        if (credential := environ.get("DUOLINGO_JWT")) is not None
        else (environ["DUOLINGO_PASSWORD"], False)
    )

    # Declare paths.
    progression_database_path = path.join("data", "duolingo-progress.json")
    statistics_database_path = path.join("data", "statistics.json")

    # Initialize required infrastructures.
    api = APIClient(base_url=base_api_url)
    progression_database = Database(filename=progression_database_path)
    statistics_database = Database(filename=statistics_database_path)

    # If the supplied credential is the password, login to Duolingo first.
    token, passwordless = (
        (credential, True) if passwordless else (api.login(username, credential), False)
    )

    # Get the possible data.
    raw_user, raw_summary = api.fetch_data(username, token)

    # Transform them into our internal schema.
    user = User.to_user(raw_user)
    summaries = [Summary(**summary) for summary in raw_summary["summaries"]]

    # Get all existing data from the database. Add the new data to the end of the database
    # declaratively. `0` means the first entry, or today (when the script is run).
    database_entries = [
        *[DatabaseEntry(**entry) for entry in progression_database.get()],
        DatabaseEntry.create_now(summaries[0], user.site_streak),
    ]

    # Synchronize the database with the summaries.
    synchronized_database = sync_database_with_summaries(database_entries, summaries)

    # Check whether we have synchronized the data or not.
    is_database_changed = check_database_change(synchronized_database, database_entries)

    # Store the synchronized database in our repository.
    progression_database.set(
        [DatabaseEntry.to_dict(entry) for entry in synchronized_database]
    )

    # On the other hand, get all of the statistics of the cron run, and then immutably
    # add the current cron statistics.
    statistics_entries = Statistics(
        datetime={
            **statistics_database.get()["datetime"],
            **Statistics.create_datetime_now(),
        }
    )

    # Store the statistics in our repository.
    statistics_database.set(Statistics.to_dict(statistics_entries))

    # Return flags from the program to consolidate the print statements in the outer loop,
    # minimizing side effects.
    return passwordless, is_database_changed


def main() -> None:
    log("Script is starting and running now.")
    try:
        passwordless, is_database_changed = run()
        match passwordless:
            case True:
                log("Script authenticated with your JWT.")
            case False:
                log("Script authenticated with your password. Please change it to JWT.")

        match is_database_changed:
            case True:
                log(
                    "Script found discrepancies between current data and online data. Synchronization is done automatically."
                )
            case False:
                log(
                    "Script did not find discrepancies between current data and online data. Synchronization not required."
                )

        log(
            "Script run successfully! Please check the specified path to see your newly updated data."
        )
    except ValidationError as error:
        log(
            f"Error encountered when parsing data. Potentially, a breaking API change: {error}"
        )
    except (
        CaptchaException,
        LoginException,
        NotFoundException,
        UnauthorizedException,
    ) as error:
        log(f"{error.__class__.__name__}: {error}")
    except Exception as error:
        log(f"Unexpected Exception: {error.__class__.__name__}: {error}")
        log(format_exc())
    finally:
        log("Japanese Duolingo Visualizer script has finished running.")


if __name__ == "__main__":
    main()
