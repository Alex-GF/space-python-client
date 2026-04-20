from __future__ import annotations

import pytest

from space_client import SpaceClientFactory
from space_client.types import SpaceConnectionOptions


def test_connect_with_valid_options():
    client = SpaceClientFactory.connect(
        SpaceConnectionOptions(url="http://localhost:8080", api_key="test-api-key")
    )
    assert client is not None


def test_connect_with_overload_url_and_api_key():
    client = SpaceClientFactory.connect("http://localhost:8080", "test-api-key")
    assert client is not None


def test_should_fail_with_missing_options_fields():
    with pytest.raises(ValueError, match="URL is required"):
        SpaceClientFactory.connect(SpaceConnectionOptions(url="", api_key="test-api-key"))

    with pytest.raises(ValueError, match="API key is required"):
        SpaceClientFactory.connect(SpaceConnectionOptions(url="http://localhost:8080", api_key=""))


def test_should_fail_with_invalid_timeout():
    with pytest.raises(ValueError, match="Invalid timeout value"):
        SpaceClientFactory.connect(
            SpaceConnectionOptions(url="http://localhost:8080", api_key="test-api-key", timeout=0)
        )


def test_should_fail_with_invalid_scheme():
    with pytest.raises(ValueError, match="Invalid URL"):
        SpaceClientFactory.connect(
            SpaceConnectionOptions(url="ftp://localhost:8080", api_key="test-api-key")
        )
