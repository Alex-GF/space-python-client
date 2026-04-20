from __future__ import annotations

from .space_client import SpaceClient
from .types.space_connection_options import SpaceConnectionOptions


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

        return SpaceClient(options)
