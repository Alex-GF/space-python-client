"""The return type of a call that exists in both a sync and an async client.

A module's methods are written once and run by either runner, so what they hand
back is the value on the synchronous client and an awaitable of that value on
the asynchronous one. ``Result[T]`` says exactly that, which keeps one set of
signatures honest for both without writing them twice.
"""

from __future__ import annotations

from typing import Awaitable, TypeVar, Union

T = TypeVar("T")

Result = Union[T, Awaitable[T]]
