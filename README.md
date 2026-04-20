# Space Python Client

Python client library for [Space](https://github.com/isa-group/space), a pricing-driven self-adaptation platform for SaaS applications.

[![PyPI](https://img.shields.io/pypi/v/space-python-client.svg)](https://pypi.org/project/space-python-client)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Table of Contents

- [What You Get](#what-you-get)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start in 5 Minutes](#quick-start-in-5-minutes)
- [Configuration](#configuration)
- [API Overview](#api-overview)
- [Data Models](#data-models)
- [Caching](#caching)
- [WebSocket Events](#websocket-events)
- [Error Handling](#error-handling)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## What You Get

- Simple API to connect to Space.
- Contract lifecycle operations.
- Feature evaluation with optional expected consumption.
- Revert operation for optimistic usage updates.
- Pricing token generation.
- Built-in in-memory cache and optional Redis cache.
- WebSocket events for real-time pricing updates.

## Requirements

- Python 3.10+

## Installation

```bash
pip install space-python-client
```

Optional Redis support:

```bash
pip install "space-python-client[redis]"
```

## Quick Start in 5 Minutes

```python
from space_client import SpaceClientFactory

client = SpaceClientFactory.connect(
	"http://localhost:3000",
	"your-api-key",
	10_000,
)

healthy = client.is_connected_to_space()
print(f"Connected: {healthy}")

result = client.features.evaluate("user-123", "serviceA-featureX")
if result.error is not None:
	print(f"Evaluation error: {result.error.message}")
else:
	print(f"Feature enabled: {result.eval}")

pricing_token = client.features.generate_user_pricing_token("user-123")
print(f"Pricing token: {pricing_token}")

client.close()
```

## Configuration

You can connect using either convenience factory arguments or `SpaceConnectionOptions`.

### Option A: simple connection

```python
from space_client import SpaceClientFactory

client = SpaceClientFactory.connect("http://localhost:3000", "your-api-key")
```

### Option B: custom timeout

```python
client = SpaceClientFactory.connect("http://localhost:3000", "your-api-key", 15000)
```

### Option C: full options object

```python
from space_client import SpaceClientFactory
from space_client.types import CacheOptions, SpaceConnectionOptions

options = SpaceConnectionOptions(
	url="http://localhost:3000",
	api_key="your-api-key",
	timeout=15000,
	cache=CacheOptions(enabled=True),
)

client = SpaceClientFactory.connect(options)
```

`SpaceClientFactory.connect(...)` validation rules:

- URL is required and must start with `http://` or `https://`.
- API key is required.
- Timeout must be a positive number.

## API Overview

### SpaceClientFactory

| Method | Description |
|---|---|
| `connect(options)` | Creates a client from full options and validates required inputs. |
| `connect(url, api_key)` | Convenience overload with default timeout (`5000`). |
| `connect(url, api_key, timeout)` | Convenience overload with custom timeout. |

### SpaceClient

Main entry point. Exposes modules as public fields:

- `contracts`
- `features`
- `cache`

Core methods:

| Method | Returns | Details |
|---|---|---|
| `is_connected_to_space()` | `bool` | HTTP health check against `/healthcheck`. |
| `on(event, callback)` | `None` | Registers event callback for supported event names. |
| `remove_listener(event)` | `None` | Removes one callback by event name. |
| `remove_all_listeners()` | `None` | Removes all event callbacks. |
| `connect()` | `None` | Connects/reconnects WebSocket namespace if disconnected. |
| `disconnect()` | `None` | Disconnects WebSocket namespace. |
| `close()` | `None` | Closes sockets, cache provider, and HTTP resources. |

Java-style aliases are also available (`isConnectedToSpace`, `removeListener`, `removeAllListeners`, etc.).

### ContractModule

| Method | Returns |
|---|---|
| `get_contract(user_id)` | `Contract | None` |
| `add_contract(contract_to_create)` | `Contract | None` |
| `update_contract_subscription(user_id, new_subscription)` | `Contract | None` |
| `update_contract_subscription_by_group_id(group_id, new_subscription)` | `list[Contract] | None` |
| `update_contract_usage_levels(user_id, service_name, usage_levels_novations)` | `Contract | None` |
| `remove_contract(user_id)` | `None` |

Java-style aliases are also available (`getContract`, `addContract`, etc.).

### FeatureModule

| Method | Returns |
|---|---|
| `evaluate(user_id, feature_id, expected_consumption=None, details=False, server=False)` | `FeatureEvaluationResult` |
| `revert_evaluation(user_id, feature_id, revert_to_latest=True)` | `bool` |
| `generate_user_pricing_token(user_id)` | `str | None` |

Java-style aliases are also available (`revertEvaluation`, `generateUserPricingToken`).

## Data Models

Main model classes are exported from `space_client.types`:

- `SpaceConnectionOptions`
- `CacheOptions`, `CacheType`, `ExternalCacheConfig`, `RedisConfig`
- `Contract`, `ContractToCreate`, `Subscription`
- `FeatureEvaluationResult`, `EvaluationError`
- `BillingPeriod`, `BillingPeriodToCreate`, `ContractHistoryEntry`, `UsageLevel`, `UserContact`
- `SpaceEvent`

## Caching

Built-in cache is enabled with:

```python
from space_client.types import CacheOptions, SpaceConnectionOptions

options = SpaceConnectionOptions(
	url="http://localhost:3000",
	api_key="your-api-key",
	cache=CacheOptions(enabled=True),
)
```

Redis cache example:

```python
from space_client.types import (
	CacheOptions,
	CacheType,
	ExternalCacheConfig,
	RedisConfig,
	SpaceConnectionOptions,
)

options = SpaceConnectionOptions(
	url="http://localhost:3000",
	api_key="your-api-key",
	cache=CacheOptions(
		enabled=True,
		type=CacheType.REDIS,
		external=ExternalCacheConfig(
			redis=RedisConfig(host="localhost", port=6379),
		),
		ttl=300,
	),
)
```

## WebSocket Events

Supported event names:

- `synchronized`
- `pricing_created`
- `pricing_archived`
- `pricing_actived`
- `service_disabled`
- `error`

Example:

```python
def on_pricing_created(details):
	print("Pricing changed:", details)


client.on("pricing_created", on_pricing_created)
client.connect()
```

## Error Handling

- Factory validation raises `ValueError` for invalid input.
- Runtime HTTP failures are converted to `None`/`False` return values where appropriate.
- `FeatureModule.evaluate(...)` returns an object containing `error` when request handling fails.

## Testing

Run tests locally:

```bash
pip install -e .[dev]
pytest
```

CI executes tests on every pull request for Python `3.10`, `3.11`, and `3.12`.

## Contributing

1. Create a branch from `main`.
2. Add or update tests for every behavior change.
3. Open a pull request.

## License

MIT License.
