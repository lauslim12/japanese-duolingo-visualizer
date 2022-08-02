"""
Custom API Client for Duolingo. This is necessary to access your own statistics in your Duolingo account.

Essentially, there are three endpoints that will be used during the lifecycle of this API helper, which are:
- `https://www.duolingo.com/login` -- to log in to the API.
- `https://www.duolingo.com/users/<USERNAME>` -- to access the currently logged in user's data.
- `https://www.duolingo.com/2017-06-30/users/<UID>` -- to access the currently logged in user's streak information and today's points / experience gained.

Please use this code responsibly and do not spam Duolingo's servers.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Literal, NoReturn, Optional, Tuple, Union

import requests


@dataclass
class Duolingo:
    """
    REST API Client for Duolingo API. Please use responsibly and do not spam their servers.
    """

    # Special exceptions to be exported.
    class CaptchaException(Exception):
        """
        Special exception for captcha responses. If this happens, it means that you
        are probably caught in their spam filter and have to change your user agent. You also
        have to log in again.
        """

    class LoginException(Exception):
        """
        Special exception if you failed to log in to the API. This means that your credentials are either wrong,
        or an internal server error happened at Duolingo's API.
        """

    class NotFoundException(Exception):
        """
        Exception that will be thrown if the API returns a `404 Not Found`.
        """

    class UnauthorizedException(Exception):
        """
        Exception that will be thrown if the API returns a `401 Unauthorized`.
        """

    # Base URL of Duolingo's API.
    BASE_URL = "https://www.duolingo.com"

    # Class members to be initialized in the `__init__` method. Remember, this is a `@dataclass`. For usage, it is recommended
    # that you treat this like inserting `**kwargs`-style arguments.
    username: str
    password: Optional[str]
    jwt: Optional[str]
    session = requests.Session()
    daily_progress: dict[str, Any]
    user_data: dict[str, Any]
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"

    def request(
        self,
        url: str,
        data: Optional[dict[str, Any]] = None,
    ) -> requests.Response:
        """
        Used to perform a request / API call to Duolingo's API. Handles all possible errors I could
        think of, with the proper authorization (network headers) and request body.
        """
        # Creates required network headers to perform authenticated requests.
        headers = {
            "Authorization": f"Bearer {self.jwt}" if self.jwt is not None else "",
            "User-Agent": self.user_agent,
        }

        # Prepare request.
        request = requests.Request(
            method="POST" if data else "GET",
            url=url,
            json=data,
            headers=headers,
            cookies=self.session.cookies,
        )

        # Send request.
        response = self.session.send(request.prepare())

        # Handle several errors: `401` and `404`.
        if response.status_code == 401:
            raise self.UnauthorizedException(
                f"You are not authorized to access the resource with URL: '{url}'. Please try again with the correct credentials."
            )
        elif response.status_code == 404:
            raise self.NotFoundException(
                "The resource that you are looking for is not found."
            )

        # Handle an edge case: captcha lock-out!
        if (
            response.status_code == 403
            and response.json().get("blockScript") is not None
        ):
            raise self.CaptchaException(
                f"Request to '{url}' with user agent '{self.user_agent}' was blocked, and the API requests you to solve a captcha. Please try logging in again with a different user agent."
            )

        # Return proper response object.
        return response

    def login(self) -> Union[Tuple[str, Literal["password", "jwt"]], NoReturn]:
        """
        Logs in to the Duolingo API. Steps:
        - If the user does not have a JWT, they will be logged in with their `username` and `password`.
        - Populates the whole `user_data` and `daily_progress` dictionary.

        Please store the JWT (returned from this function) after this function returns. This is
        intentionally done to prevent side-effects, keeping this function as pure as possible.
        """
        # Log in properly if the user does not have any JWT.
        if not self.jwt:
            response = self.request(
                f"{self.BASE_URL}/login",
                data={
                    "login": self.username,
                    "password": self.password,
                },
            )
            if "failure" in response.json():
                raise self.LoginException(
                    "Failed to log in with your current credentials. Please check it and try again later."
                )

            # Inject our JWT for subsequent requests in the same session.
            self.jwt = response.headers["jwt"]

        # Populate our `user_data` and `daily_progress` class attribute via API requests.
        self.user_data = self.request(f"{self.BASE_URL}/users/{self.username}").json()
        self.daily_progress = self.request(
            f"{self.BASE_URL}/2017-06-30/users/{self.user_data['id']}"
        ).json()

        # Return our JWT.
        return self.jwt

    def get_words(self) -> list[str]:
        """
        Gets all words one has learned. This process is done by querying the `user_data` class attribute.
        """
        words = []
        for topic in self.user_data["language_data"]["ja"]["skills"]:
            if topic["learned"]:
                words += topic["words"]

        return list(set(words))

    def get_daily_experience_progress(self) -> dict[str, str]:
        """
        Gets daily experience progress. This process is done by querying the `daily_progress` class attribute.
        """
        # `xpGains` lists the lessons completed on the last day where lessons were done.
        # We use the `streakData.updatedTimestamp`` to get the last "midnight", and get lessons after that.
        reported_timestamp = self.daily_progress["streakData"]["updatedTimestamp"]
        reported_midnight = datetime.fromtimestamp(reported_timestamp)
        midnight = datetime.fromordinal(datetime.today().date().toordinal())

        # Sometimes the update is marked into the future. When this is the case
        # we fall back on the system time for midnight.
        time_discrepancy = min(midnight - reported_midnight, timedelta(0))
        update_cutoff = round((reported_midnight + time_discrepancy).timestamp())
        lessons = [
            lesson
            for lesson in self.daily_progress["xpGains"]
            if lesson["time"] > update_cutoff
        ]

        return {
            "xp_goal": self.daily_progress["xpGoal"],
            "xp_today": sum(x["xp"] for x in lessons),
        }

    def get_streak_info(self) -> dict[str, str]:
        """
        Gets current information about our daily streak from Duolingo. This process is done by querying the `user_data`
        class attribute.
        """
        return {
            "site_streak": self.user_data["site_streak"],
            "streak_extended_today": self.user_data["streak_extended_today"],
        }
