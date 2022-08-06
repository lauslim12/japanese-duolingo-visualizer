"""Main runner, expected to be run as a command line program."""

from datetime import datetime
from os import environ, path

from src.duolingo import Duolingo
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

        # Shape our data.
        progress = {
            "date": datetime.now().strftime("%Y/%m/%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "experience": lingo.get_daily_experience_progress(),
            "session_information": lingo.get_session_time(),
            "streak_information": lingo.get_streak_info(),
            # This is large and can cause the JSON to bloat, as everyday I always learn new words.
            # "learned_words": lingo.get_words(),
            "number_of_learned_words": len(lingo.get_words()),
        }

        # Print a message.
        print(
            "[JDV] Japanese Duolingo Visualizer script has successfully fetched the necessary information!"
        )

        # Save them to JSON.
        store = Store(progress, path.join("data", "duolingo-progress.json"), [])
        store.get_from_json_file()
        store.process_json_data()
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
    finally:
        print("[JDV] Japanese Duolingo Visualizer script has finished running.")


if __name__ == "__main__":
    main()
