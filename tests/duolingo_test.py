"""Tests for our Duolingo API client."""


import pytest
import requests_mock

from src.duolingo import Duolingo


@pytest.fixture()
def duolingo():
    return Duolingo(
        username="test",
        password="",
        jwt="",
        user_data={
            "id": 1,
            "language_data": {
                "ja": {
                    "skills": [
                        {
                            "learned": True,
                            "words": [
                                "水",
                                "独学",
                                "ナルト",
                                "楓",
                                "進歩",
                                "勉強",
                                "四月",
                                "口",
                                "力",
                                "先生",
                            ],
                        },
                    ]
                }
            },
            "site_streak": 5,
        },
        daily_experience_progress={
            "summaries": [
                {
                    "date": 1659657600,
                    "numSessions": 1,
                    "gainedXp": 150,
                    "frozen": False,
                    "repaired": False,
                    "streakExtended": True,
                    "userId": 1,
                    "dailyGoalXp": 50,
                    "totalSessionTime": 1,
                },
                {
                    "date": 1659571200,
                    "numSessions": 1,
                    "gainedXp": 200,
                    "frozen": False,
                    "repaired": False,
                    "streakExtended": True,
                    "userId": 1,
                    "dailyGoalXp": 50,
                    "totalSessionTime": 1,
                },
            ]
        },
    )


@pytest.mark.usefixtures("duolingo")
class TestDuolingo:
    # `requests_mock` does not need to be a fixture: https://requests-mock.readthedocs.io/en/latest/pytest.html.
    def test_request(self, duolingo: Duolingo, requests_mock: requests_mock.Mocker):
        url = "https://example.com"

        # 1. Ensures this function works properly.
        requests_mock.get(url, status_code=200, text="ok")
        assert 200 == duolingo.request(url).status_code
        assert "ok" == duolingo.request(url).text

        # 2. Mocking: 401.
        requests_mock.get(url, status_code=401, text="unauthorized")
        with pytest.raises(duolingo.UnauthorizedException):
            duolingo.request(url)

        # 3. Mocking: 404.
        requests_mock.get(url, status_code=404, text="not found")
        with pytest.raises(duolingo.NotFoundException):
            duolingo.request(url)

        # 4. Mocking: 403 and Captcha.
        requests_mock.get(url, status_code=403, text='{"blockScript": "sample"}')
        with pytest.raises(duolingo.CaptchaException):
            duolingo.request(url)

    def test_login(self, duolingo: Duolingo, requests_mock: requests_mock.Mocker):
        login_url = f"{duolingo.BASE_URL}/login"
        data_url = f"{duolingo.BASE_URL}/users/{duolingo.username}"
        daily_url = f"{duolingo.BASE_URL}/2017-06-30/users/{duolingo.user_data['id']}/xp_summaries?startDate=1970-01-01"
        expected_jwt = "token"

        # 1. Mock the login session (failure). For context: our class and our `login` function
        # here is not pure, so if we test the successful case first, `self.jwt` would have been
        # defined with `token`, hence making this case 'unable to fail' and of course in terms of
        # unit testing, this is not good.
        requests_mock.post(login_url, text='{"failure": "here"}')
        with pytest.raises(duolingo.LoginException):
            duolingo.login()

        # 2. Now we ensure that our function works properly. There is a bit of a side effect:
        # The function mutates the `user_data`, and it will cause 'id' to be `None` in the next `daily_url`
        # step. That's why we intentionally wrote the JSON response's `id` as `1` (we are making them the
        # same as the initial constructor for ease of testing). For easier-to-understand version:
        #
        # - Log in.
        # - Gets the user data, set the mock response's `id` attribute to `1` so it can be used in the next API call.
        # - Gets the daily progress data (to get our progress, we need that `id` attribute!).
        requests_mock.post(login_url, text='{"jwt": "token"}', headers={"jwt": "token"})
        requests_mock.get(data_url, text='{"id": 1}')
        requests_mock.get(daily_url, text='{"sample": "success json"}')

        # Ensures everything works correctly.
        actual_jwt = duolingo.login()
        assert expected_jwt == actual_jwt

    def test_get_words(self, duolingo: Duolingo):
        expected_words = ["水", "独学", "ナルト", "楓", "進歩", "勉強", "四月", "口", "力", "先生"]

        actual_words = duolingo.get_words()
        assert len(expected_words) == len(actual_words)
        assert not set(expected_words) ^ set(actual_words)

    def test_get_daily_experience_points(self, duolingo: Duolingo):
        expected_xp_goal = 50
        expected_xp_today = 150

        actual_daily_experience_progress = duolingo.get_daily_experience_progress()
        assert actual_daily_experience_progress["xp_goal"] == expected_xp_goal
        assert actual_daily_experience_progress["xp_today"] == expected_xp_today

    def test_get_streak(self, duolingo: Duolingo):
        expected_site_streak = 5

        actual_streak_info = duolingo.get_streak_info()
        assert actual_streak_info["site_streak"] == expected_site_streak
