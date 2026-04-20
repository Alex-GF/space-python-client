from __future__ import annotations

import pytest


class FakeSocketClient:
    def __init__(self, *args, **kwargs):
        self.connected = False
        self._handlers: dict[tuple[str, str | None], callable] = {}

    def on(self, event: str, namespace: str | None = None):
        def decorator(func):
            self._handlers[(event, namespace)] = func
            return func

        return decorator

    def connect(self, *args, **kwargs):
        self.connected = True

    def disconnect(self):
        self.connected = False

    def trigger(self, event: str, data=None, namespace: str | None = "/pricings"):
        handler = self._handlers.get((event, namespace))
        if handler is None:
            return
        if data is None:
            handler()
        else:
            handler(data)


@pytest.fixture(autouse=True)
def patch_socketio_client(monkeypatch):
    from space_client import space_client as client_module

    monkeypatch.setattr(client_module.socketio, "Client", FakeSocketClient)
