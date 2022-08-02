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
            "streak_extended_today": True,
        },
        daily_progress={
            "streakData": {
                "updatedTimestamp": 1659330000,
            },
            "xpGains": [
                {
                    "eventType": "TEST",
                    "xp": 20,
                    "skillId": None,
                    "time": 1659004150,
                },
                {
                    "eventType": "PRACTICE",
                    "xp": 30,
                    "skillId": None,
                    "time": 1659356238,
                },
                {
                    "eventType": "LESSON",
                    "xp": 30,
                    "skillId": None,
                    "time": 1659351896,
                },
                {
                    "eventType": "LESSON",
                    "xp": 20,
                    "skillId": None,
                    "time": 1659352087,
                },
                {
                    "eventType": "LESSON",
                    "xp": 70,
                    "skillId": None,
                    "time": 1659352255,
                },
            ],
            "xpGoal": 50,
        },
    )


@pytest.mark.usefixtures("duolingo")
class TestDuolingo:
    # `requests_mock` does not need to be a fixture: https://requests-mock.readthedocs.io/en/latest/pytest.html.
    def test_request(self, duolingo: Duolingo, requests_mock: requests_mock.Mocker):
        url = "https://example.com"

        # 1. Ensures this function works properly.
        expected_status_code, expected_response = 200, "sample response"
        requests_mock.get(url, status_code=200, text="sample response")
        assert expected_status_code == duolingo.request(url).status_code
        assert expected_response == duolingo.request(url).text

        # 2. Mocking: 401.
        expected_status_code, expected_response = 401, "unauthorized"
        requests_mock.get(url, status_code=401, text="unauthorized")
        with pytest.raises(Exception) as execinfo:
            assert expected_status_code == duolingo.request(url).status_code
        assert execinfo.type == duolingo.UnauthorizedException

        # 3. Mocking: 404.
        expected_status_code, expected_response = 404, "not found"
        requests_mock.get(url, status_code=404, text="not found")
        with pytest.raises(Exception) as execinfo:
            assert expected_status_code == duolingo.request(url).status_code
        assert execinfo.type == duolingo.NotFoundException

        # 4. Mocking: 403 and Captcha.
        expected_status_code, expected_response = 403, '{"blockScript": "sample"}'
        requests_mock.get(url, status_code=403, text='{"blockScript": "sample"}')
        with pytest.raises(Exception) as execinfo:
            assert expected_status_code == duolingo.request(url).status_code
            assert expected_response == duolingo.request(url).text
        assert execinfo.type == duolingo.CaptchaException

    def test_login(self, duolingo: Duolingo, requests_mock: requests_mock.Mocker):
        login_url = f"{duolingo.BASE_URL}/login"
        data_url = f"{duolingo.BASE_URL}/users/{duolingo.username}"
        daily_url = f"{duolingo.BASE_URL}/2017-06-30/users/{duolingo.user_data['id']}"
        expected_jwt = "token"

        # Mock the login session (failure). For context: our class and our `login` function
        # here is not pure, so if we test the successful case first, `self.jwt` would have been
        # defined with `token`, hence making this case 'unable to fail' and of course in terms of
        # unit testing, this is not good.
        with pytest.raises(Exception) as error:
            requests_mock.post(login_url, text='{"failure": "here"}')
            duolingo.login()

        assert error.type == duolingo.LoginException

        # Now we ensure that our function works properly.
        requests_mock.post(login_url, text='{"jwt": "token"}', headers={"jwt": "token"})

        # Below is another side effect: the function mutates the `user_data`, and it will cause 'id' to be
        # undefined in the next `daily_url` step. That's why we intentionally wrote the JSON response's
        # `id` as `1` (we are making them the same as the initial constructor).
        requests_mock.get(data_url, text='{"id": 1}')
        requests_mock.get(daily_url, text='{"sample": "success json"}')
        assert expected_jwt == duolingo.login()

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
        expected_streak_extended = True

        actual_streak_info = duolingo.get_streak_info()
        assert actual_streak_info["site_streak"] == expected_site_streak
        assert actual_streak_info["streak_extended_today"] == expected_streak_extended
