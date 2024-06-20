import pytest

from src.api import (
    APIClient,
    CaptchaException,
    LoginException,
    NotFoundException,
    UnauthorizedException,
)


@pytest.fixture
def client():
    return APIClient(base_url="https://example.com")


def test_login(client, requests_mock):
    mock_response = {"status": "success"}
    mock_response_headers = {"jwt": "fake_jwt_token"}
    requests_mock.post(
        "https://example.com/login",
        json=mock_response,
        headers=mock_response_headers,
    )

    token = client.login("my_username", "my_password")
    assert token == "fake_jwt_token"


def test_login_exception(client, requests_mock):
    mock_response = {"failure": "error"}
    requests_mock.post(
        "https://example.com/login",
        json=mock_response,
    )
    with pytest.raises(LoginException):
        client.login("my_username", "my_password")


def test_fetch_data(client, requests_mock):
    token = "fake_jwt_token"
    mock_user_response = {"id": "1", "username": "my_username"}
    requests_mock.get(
        "https://example.com/users/my_username",
        request_headers={"Authorization": f"Bearer {token}"},
        json=mock_user_response,
    )

    mock_summary_response = {"summaries": []}
    requests_mock.get(
        "https://example.com/2017-06-30/users/1/xp_summaries?startDate=1970-01-01",
        request_headers={"Authorization": f"Bearer {token}"},
        json=mock_summary_response,
    )

    raw_user, raw_summary = client.fetch_data("my_username", token)
    assert raw_user == {"id": "1", "username": "my_username"}
    assert raw_summary == {"summaries": []}


@pytest.mark.parametrize(
    "status_code, json_data, expected_exception",
    [
        (401, {}, UnauthorizedException),
        (403, {"blockScript": True}, CaptchaException),
        (404, {}, NotFoundException),
    ],
)
def test_request_exceptions(
    client, status_code, json_data, expected_exception, requests_mock
):
    requests_mock.get("https://example.com", status_code=status_code, json=json_data)
    with pytest.raises(expected_exception):
        client.request("https://example.com")
