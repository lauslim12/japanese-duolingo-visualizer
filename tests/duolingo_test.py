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
                    "numSessions": 10,
                    "gainedXp": 150,
                    "frozen": False,
                    "repaired": False,
                    "streakExtended": True,
                    "userId": 1,
                    "dailyGoalXp": 50,
                    "totalSessionTime": 5400,
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
        expected_jwt = "token"

        # 1. Mock the login session (failure). For context: our class and our `login` function
        # here is not pure, so if we test the successful case first, `self.jwt` would have been
        # defined with `token`, hence making this case 'unable to fail' and of course in terms of
        # unit testing, this is not good.
        requests_mock.post(login_url, text='{"failure": "here"}')
        with pytest.raises(duolingo.LoginException):
            duolingo.login()

        # 2. Now we ensure that our login works properly with the proper return values.
        requests_mock.post(login_url, text='{"jwt": "token"}', headers={"jwt": "token"})
        actual_jwt = duolingo.login()

        # Ensures everything works correctly.
        assert expected_jwt == actual_jwt
        assert duolingo.login_method == "Password"

    def test_login_method(
        self, duolingo: Duolingo, requests_mock: requests_mock.Mocker
    ):
        login_url = f"{duolingo.BASE_URL}/login"
        duolingo.jwt = "I already have a JWT"

        # Login with existing JWT.
        requests_mock.post(login_url, headers={"jwt": duolingo.jwt})
        duolingo.login()

        # Ensure that everything is as expected.
        assert duolingo.login_method == "JWT"

    def test_fetch_data(self, duolingo: Duolingo, requests_mock: requests_mock.Mocker):
        data_url = f"{duolingo.BASE_URL}/users/{duolingo.username}"
        daily_url = f"{duolingo.BASE_URL}/2017-06-30/users/{duolingo.user_data['id']}/xp_summaries?startDate=1970-01-01"

        # Make API requests.
        requests_mock.get(data_url, text='{"id": 1}')
        requests_mock.get(daily_url, text='{"sample": "success json"}')
        user_data, daily_experience_progress = duolingo.fetch_data()

        # Ensure everything is as expected.
        assert duolingo.user_data == user_data
        assert duolingo.daily_experience_progress == daily_experience_progress

    def test_get_summaries(self, duolingo: Duolingo):
        expected_summary = [
            {
                "date": 1659657600,
                "daily_goal_xp": 50,
                "gained_xp": 150,
                "num_sessions": 10,
                "total_session_time": 5400,
            },
            {
                "date": 1659571200,
                "daily_goal_xp": 50,
                "gained_xp": 200,
                "num_sessions": 1,
                "total_session_time": 1,
            },
        ]

        actual = [summary.model_dump() for summary in duolingo.get_summaries()]
        assert len(expected_summary) == len(actual)
        assert expected_summary == actual

    def test_get_user_data(self, duolingo: Duolingo):
        expected_user_data = {"site_streak": 5}

        actual = duolingo.get_user_data().model_dump()
        assert actual == expected_user_data
