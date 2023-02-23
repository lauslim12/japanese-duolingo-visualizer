"""Main runner, expected to be run as a command line program."""

from copy import deepcopy
from datetime import datetime
from os import environ, path
from traceback import format_exc
from typing import Any, Tuple

from src.duolingo import Duolingo
from src.store import Store


def synchronize_xp_and_time(
    json_data: list[dict[str, Any]], daily_progression: list[dict[str, Any]]
) -> Tuple[list[dict[str, Any]], bool]:
    """
    Synchronizes own data with Duolingo's API for data we cannot have any disparities/differences with. The
    time complexity of this function is O(N^2).

    Keep in mind that `progression["time"]` is in UNIX timestamp, so it has to be converted into your usual
    `YYYY-MM-DD` format so it uniforms with our own data.
    """
    new_json_data = deepcopy(json_data)
    changed = False

    for i, data in enumerate(json_data):
        for progression in daily_progression["summaries"]:
            progression_time = datetime.fromtimestamp(progression["date"]).strftime(
                "%Y/%m/%d"
            )

            if data["date"] == progression_time:
                # If found differences in `xp_today`.
                if data["experience"]["xp_today"] != progression["gainedXp"]:
                    new_json_data[i]["experience"]["xp_today"] = progression["gainedXp"]
                    changed = True

                # If found differences in `session_time`.
                if (
                    data["session_information"]["session_time"]
                    != progression["totalSessionTime"]
                ):
                    new_json_data[i]["session_information"][
                        "session_time"
                    ] = progression["totalSessionTime"]
                    changed = True

                # If found differences in `number_of_sessions`.
                if (
                    data["session_information"]["number_of_sessions"]
                    != progression["numSessions"]
                ):
                    new_json_data[i]["session_information"][
                        "number_of_sessions"
                    ] = progression["numSessions"]
                    changed = True

    return new_json_data, changed


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
            f"[JDV] Japanese Duolingo Visualizer script has logged in to your account with {lingo.login_method} method."
        )

        # Shape our data.
        progress = {
            "date": datetime.now().strftime("%Y/%m/%d"),
            "experience": lingo.get_daily_experience_progress(),
            # This is large and can cause the JSON to bloat, as everyday I always learn new words.
            # For now, this is commented.
            # "learned_words": lingo.get_words(),
            "number_of_learned_words": len(lingo.get_words()),
            "session_information": lingo.get_session_info(),
            "streak_information": lingo.get_streak_info(),
            "time": datetime.now().strftime("%H:%M:%S"),
        }

        # Print a message.
        print(
            "[JDV] Japanese Duolingo Visualizer script has successfully fetched the necessary information!"
        )

        # Prepare a file to take and store our data from/to.
        store = Store(progress, path.join("data", "duolingo-progress.json"), [])
        store.get_from_json_file()
        store.process_json_data()

        # Synchronize our data, especially XP and session time.
        new_data, changed = synchronize_xp_and_time(
            store.json_content, lingo.daily_experience_progress
        )
        if changed:
            print(
                "[JDV] Japanese Duolingo Visualizer script has synchronized your data."
            )

        # Stores our data to a file.
        store.json_content = new_data
        store.store_to_json_file()

        # Print success message.
        print(
            "[JDV] Japanese Duolingo Visualizer script is successful! Please check your specified `filename` path to see your newly updated data."
        )
    except (
        Duolingo.CaptchaException,
        Duolingo.LoginException,
        Duolingo.NotFoundException,
        Duolingo.UnauthorizedException,
    ) as error:
        print(f"[JDV] {error.__class__.__name__}: {error}")
    except Exception as error:
        print(f"[JDV] Unexpected Exception: {error.__class__.__name__}: {error}")
        print(format_exc())
    finally:
        print("[JDV] Japanese Duolingo Visualizer script has finished running.")


if __name__ == "__main__":
    main()
