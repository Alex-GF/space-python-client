from __future__ import annotations

from typing import Any, Callable

import httpx
import socketio

from .modules.cache_module import CacheModule
from .modules.contract_module import ContractModule
from .modules.feature_module import FeatureModule
from .errors import SpaceApiError, SpaceConnectionError
from .types.space_connection_options import SpaceConnectionOptions
from .types.space_event import SpaceEvent


def _read_body(response) -> Any:
    """Whatever Space sent with a refusal, JSON if it parses and text if not.

    Never raises: this runs while an error is being built, and failing here
    would replace a useful message with a confusing one.
    """
    try:
        return response.json()
    except Exception:
        try:
            return response.text
        except Exception:
            return None


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
        """Create a new Space client.

        Args:
            options (SpaceConnectionOptions): Connection settings including URL, API key,
                timeout, and optional cache configuration.

        Returns:
            None: This constructor initializes client state and modules.

        Raises:
            ValueError: If URL or API key are missing.
        """
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
        """Check Space health endpoint availability.

        Returns:
            bool: True when `/healthcheck` responds successfully with a `message` field,
            otherwise False.
        """
        payload = self._request_json("GET", "/healthcheck")
        return isinstance(payload, dict) and "message" in payload

    def on(self, event: str, callback: Callable[[Any], None]) -> None:
        """Register an event listener callback.

        Args:
            event (str): Event name. Supported values include synchronized,
                pricing_created, pricing_archived, pricing_actived,
                service_disabled, and error.
            callback (Callable[[Any], None]): Function invoked with event payload.

        Returns:
            None: Listener registration updates internal callback registry.
        """
        event_lower = event.lower()
        if event_lower in self._VALID_EVENTS:
            self._callbacks[event_lower] = callback

    def remove_listener(self, event: str) -> None:
        """Remove the callback associated with an event.

        Args:
            event (str): Event name to deregister.

        Returns:
            None: No value is returned.
        """
        event_lower = event.lower()
        if event_lower in self._VALID_EVENTS:
            self._callbacks.pop(event_lower, None)

    def remove_all_listeners(self) -> None:
        """Remove all registered callbacks.

        Returns:
            None: No value is returned.
        """
        self._callbacks.clear()

    def connect(self) -> None:
        """Open the WebSocket connection to Space pricing events.

        Returns:
            None: Connection is attempted asynchronously; failures are ignored.
        """
        if self._socket.connected:
            return
        try:
            ws_url = self._base_url.replace("http://", "ws://").replace("https://", "wss://")
            self._socket.connect(ws_url, namespaces=["/pricings"], socketio_path="events", wait=False)
        except Exception:
            # The client should still be usable in HTTP-only mode.
            return

    def disconnect(self) -> None:
        """Close active WebSocket connection.

        Returns:
            None: No value is returned.
        """
        try:
            if self._socket.connected:
                self._socket.disconnect()
        except Exception:
            return

    def close(self) -> None:
        """Release all client resources.

        Returns:
            None: No value is returned.
        """
        self.disconnect()
        self.cache.close()
        self._http_client.close()

    def get_http_url(self) -> str:
        """Get internal API URL.

        Returns:
            str: Base HTTP URL including `/api/v1` suffix.
        """
        return self._http_url

    def get_api_key(self) -> str:
        """Get configured API key.

        Returns:
            str: API key currently used by the client.
        """
        return self._api_key

    def get_timeout(self) -> int:
        """Get configured timeout.

        Returns:
            int: HTTP timeout in milliseconds.
        """
        return self._timeout

    def _send(self, method: str, path: str, json: Any | None = None):
        """Make the request, or say why it could not be made.

        A transport failure is not an answer, so it is raised rather than
        folded into one: a caller that cannot reach Space has learnt something
        different from a caller whose request was refused.
        """
        url = f"{self._http_url}{path}"
        try:
            return self._http_client.request(
                method,
                url,
                headers={"x-api-key": self._api_key},
                json=json,
            )
        except Exception as error:
            raise SpaceConnectionError(f"Could not reach Space at {url}: {error}") from error

    def _request_json(self, method: str, path: str, json: Any | None = None) -> dict[str, Any] | list[Any] | None:
        """The decoded body, or an exception saying what Space objected to.

        ``None`` now means one thing - Space answered successfully with a body
        that is not JSON - instead of standing in for a refusal, an outage and
        an empty response at once.
        """
        response = self._send(method, path, json=json)

        if response.status_code < 200 or response.status_code >= 300:
            raise SpaceApiError(response.status_code, method, path, _read_body(response))

        try:
            return response.json()
        except Exception:
            return None

    def _request_no_content(self, method: str, path: str, json: Any | None = None) -> bool:
        """Whether Space accepted a request that returns nothing.

        Still a boolean, because for these calls "did it work" is the whole
        question - but a refusal now raises, so ``False`` is no longer the
        answer to both "it declined" and "it never arrived".
        """
        response = self._send(method, path, json=json)

        if response.status_code < 200 or response.status_code >= 300:
            raise SpaceApiError(response.status_code, method, path, _read_body(response))

        return True

    # Java compatibility aliases
    isConnectedToSpace = is_connected_to_space
    removeListener = remove_listener
    removeAllListeners = remove_all_listeners
    getHttpUrl = get_http_url
    getApiKey = get_api_key
    getTimeout = get_timeout
