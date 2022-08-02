"""Tests for our Store class."""

from unittest.mock import mock_open, patch

import pytest

from src.store import Store


@pytest.fixture()
def store():
    return Store({}, "sample.json", [])


@pytest.mark.usefixtures("store")
class TestStore:
    def test_get_from_json_file(self, store: Store):
        # 1. Normal JSON error.
        open_mock = mock_open()
        with patch("src.store.open", open_mock, create=False):
            store.json_content = []
            store.get_from_json_file()

        open_mock.assert_called_with(store.filename, "r", encoding="UTF-8")

        # 2. Specific error: `EnvironmentError` (OS-based).
        open_error_mock = mock_open()
        open_error_mock.side_effect = EnvironmentError()
        with patch("src.store.open", open_error_mock):
            with pytest.raises(Exception) as error:
                store.get_from_json_file()

        assert error.type == store.StoreException

    def test_store_to_json_file(self, store: Store):
        open_mock = mock_open()
        with patch("src.store.open", open_mock, create=False):
            store.json_content = [{"hello": "world"}]
            store.store_to_json_file()

        open_mock.assert_called_with(store.filename, "w", encoding="UTF-8")

    def test_process_json_file(self, store: Store):
        store.data = {"hello": "world"}
        store.process_json_data()

        assert store.json_content == [store.data]
