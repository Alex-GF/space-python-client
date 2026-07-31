from __future__ import annotations

from .async_space_client import AsyncSpaceClient
from .space_client import SpaceClient
from .types.space_connection_options import SpaceConnectionOptions


def _validated(
    options_or_url: SpaceConnectionOptions | str,
    api_key: str | None = None,
    timeout: int | None = None,
) -> SpaceConnectionOptions:
    """Turn whatever the caller passed into options, or say what is wrong.

    Shared by both factory methods so a synchronous and an asynchronous client
    cannot come to disagree about what a valid connection looks like.
    """
    if isinstance(options_or_url, SpaceConnectionOptions):
        options = options_or_url
    else:
        options = SpaceConnectionOptions(
            url=options_or_url,
            api_key=api_key,
            timeout=timeout if timeout is not None else 5000,
        )

    if options is None:
        raise ValueError("Options cannot be null")

    if not options.url:
        raise ValueError("URL is required to connect to Space")

    if not options.api_key:
        raise ValueError("API key is required to connect to Space")

    if options.timeout <= 0:
        raise ValueError("Invalid timeout value. It must be a positive number")

    if not options.url.startswith("http://") and not options.url.startswith("https://"):
        raise ValueError("Invalid URL. It must start with 'http://' or 'https://'")

    return options


class SpaceClientFactory:
    @staticmethod
    def connect(
        options_or_url: SpaceConnectionOptions | str,
        api_key: str | None = None,
        timeout: int | None = None,
    ) -> SpaceClient:
        """Build and validate a Space client instance.

        Args:
            options_or_url (SpaceConnectionOptions | str): Either a full options object
                or a base URL string.
            api_key (str | None): API key used when `options_or_url` is a URL string.
            timeout (int | None): Timeout in milliseconds used when `options_or_url`
                is a URL string. Defaults to 5000.

        Returns:
            SpaceClient: Configured client ready for HTTP and WebSocket operations.

        Raises:
            ValueError: If URL, API key, or timeout values are invalid.
        """
        return SpaceClient(_validated(options_or_url, api_key, timeout))

    @staticmethod
    def connect_async(
        options_or_url: SpaceConnectionOptions | str,
        api_key: str | None = None,
        timeout: int | None = None,
    ) -> AsyncSpaceClient:
        """Build and validate an asynchronous Space client instance.

        The same arguments and the same validation as :meth:`connect`. The
        client it returns is not connected to the pricing-events WebSocket yet,
        since that needs an await; call ``await client.connect()`` or use the
        client as an async context manager when you want events.

        Args:
            options_or_url (SpaceConnectionOptions | str): Either a full options object
                or a base URL string.
            api_key (str | None): API key used when `options_or_url` is a URL string.
            timeout (int | None): Timeout in milliseconds used when `options_or_url`
                is a URL string. Defaults to 5000.

        Returns:
            AsyncSpaceClient: Configured client ready for HTTP operations.

        Raises:
            ValueError: If URL, API key, or timeout values are invalid.
        """
        return AsyncSpaceClient(_validated(options_or_url, api_key, timeout))

    # Java compatibility alias
    connectAsync = connect_async
