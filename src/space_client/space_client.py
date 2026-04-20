from __future__ import annotations

from typing import Any, Callable

import httpx
import socketio

from .modules.cache_module import CacheModule
from .modules.contract_module import ContractModule
from .modules.feature_module import FeatureModule
from .types.space_connection_options import SpaceConnectionOptions
from .types.space_event import SpaceEvent


class SpaceClient:
    _VALID_EVENTS = {
        SpaceEvent.SYNCHRONIZED.value,
        SpaceEvent.PRICING_CREATED.value,
        SpaceEvent.PRICING_ARCHIVED.value,
        SpaceEvent.PRICING_ACTIVED.value,
        SpaceEvent.SERVICE_DISABLED.value,
        SpaceEvent.ERROR.value,
    }

    def __init__(self, options: SpaceConnectionOptions) -> None:
        if not options.url:
            raise ValueError("URL is required")
        if not options.api_key:
            raise ValueError("API key is required")

        self._base_url = options.url.rstrip("/")
        self._http_url = f"{self._base_url}/api/v1"
        self._api_key = options.api_key
        self._timeout = options.timeout

        self._http_client = httpx.Client(timeout=self._timeout / 1000)
        self._callbacks: dict[str, Callable[[Any], None]] = {}

        self.cache = CacheModule()
        self.contracts = ContractModule(self)
        self.features = FeatureModule(self)

        if options.cache is not None and options.cache.enabled:
            try:
                self.cache.initialize(options.cache)
            except Exception:
                pass

        self._socket = socketio.Client(reconnection=True, logger=False, engineio_logger=False)
        self._configure_socket_handlers()
        self.connect()

    def _configure_socket_handlers(self) -> None:
        @self._socket.on("connect", namespace="/pricings")
        def _on_connect() -> None:
            callback = self._callbacks.get(SpaceEvent.SYNCHRONIZED.value)
            if callback is not None:
                callback(None)

        @self._socket.on("message", namespace="/pricings")
        def _on_message(data: Any) -> None:
            if not isinstance(data, dict):
                return
            code = str(data.get("code", "")).lower()
            details = data.get("details")
            callback = self._callbacks.get(code)
            if callback is not None:
                callback(details)

        @self._socket.on("connect_error", namespace="/pricings")
        def _on_connect_error(error: Any) -> None:
            callback = self._callbacks.get(SpaceEvent.ERROR.value)
            if callback is not None:
                callback(error)

    def is_connected_to_space(self) -> bool:
        payload = self._request_json("GET", "/healthcheck")
        return isinstance(payload, dict) and "message" in payload

    def on(self, event: str, callback: Callable[[Any], None]) -> None:
        event_lower = event.lower()
        if event_lower in self._VALID_EVENTS:
            self._callbacks[event_lower] = callback

    def remove_listener(self, event: str) -> None:
        event_lower = event.lower()
        if event_lower in self._VALID_EVENTS:
            self._callbacks.pop(event_lower, None)

    def remove_all_listeners(self) -> None:
        self._callbacks.clear()

    def connect(self) -> None:
        if self._socket.connected:
            return
        try:
            ws_url = self._base_url.replace("http://", "ws://").replace("https://", "wss://")
            self._socket.connect(ws_url, namespaces=["/pricings"], socketio_path="events", wait=False)
        except Exception:
            # The client should still be usable in HTTP-only mode.
            return

    def disconnect(self) -> None:
        try:
            if self._socket.connected:
                self._socket.disconnect()
        except Exception:
            return

    def close(self) -> None:
        self.disconnect()
        self.cache.close()
        self._http_client.close()

    def get_http_url(self) -> str:
        return self._http_url

    def get_api_key(self) -> str:
        return self._api_key

    def get_timeout(self) -> int:
        return self._timeout

    def _request_json(self, method: str, path: str, json: Any | None = None) -> dict[str, Any] | list[Any] | None:
        url = f"{self._http_url}{path}"
        try:
            response = self._http_client.request(
                method,
                url,
                headers={"x-api-key": self._api_key},
                json=json,
            )
            if response.status_code < 200 or response.status_code >= 300:
                return None
            return response.json()
        except Exception:
            return None

    def _request_no_content(self, method: str, path: str, json: Any | None = None) -> bool:
        url = f"{self._http_url}{path}"
        try:
            response = self._http_client.request(
                method,
                url,
                headers={"x-api-key": self._api_key},
                json=json,
            )
            return 200 <= response.status_code < 300
        except Exception:
            return False

    # Java compatibility aliases
    isConnectedToSpace = is_connected_to_space
    removeListener = remove_listener
    removeAllListeners = remove_all_listeners
    getHttpUrl = get_http_url
    getApiKey = get_api_key
    getTimeout = get_timeout
