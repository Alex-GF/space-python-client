from __future__ import annotations

from typing import Any

from space_client.space_client import SpaceClient
from space_client.types import SpaceConnectionOptions


class FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_healthcheck_and_event_handlers(monkeypatch):
    client = SpaceClient(SpaceConnectionOptions(url="http://localhost:3000", api_key="api-key"))

    def fake_request(method, url, headers=None, json=None):
        assert method == "GET"
        assert url.endswith("/api/v1/healthcheck")
        return FakeResponse(200, {"message": "ok"})

    monkeypatch.setattr(client._http_client, "request", fake_request)
    assert client.is_connected_to_space() is True

    received: list[Any] = []
    client.on("pricing_created", lambda details: received.append(details))

    client._socket.trigger("message", {"code": "pricing_created", "details": {"id": "p1"}})
    assert received == [{"id": "p1"}]

    client.remove_listener("pricing_created")
    client._socket.trigger("message", {"code": "pricing_created", "details": {"id": "p2"}})
    assert received == [{"id": "p1"}]


def test_close_disconnects_socket_and_http_client(monkeypatch):
    client = SpaceClient(SpaceConnectionOptions(url="http://localhost:3000", api_key="api-key"))
    marker = {"closed": False}

    def fake_close():
        marker["closed"] = True

    monkeypatch.setattr(client._http_client, "close", fake_close)
    client.close()
    assert marker["closed"] is True
