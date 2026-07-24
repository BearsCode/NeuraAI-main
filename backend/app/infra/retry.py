from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

import httpx

ResultT = TypeVar("ResultT")

_TRANSIENT_ERRORS = (
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.RemoteProtocolError,
    httpx.HTTPStatusError,
    ConnectionError,
    TimeoutError,
)


async def async_retry(
    operation: Callable[[], Awaitable[ResultT]],
    *,
    retries: int,
    base_delay_seconds: float = 0.5,
    max_delay_seconds: float = 30.0,
    retryable_exceptions: tuple[type[Exception], ...] = _TRANSIENT_ERRORS,
) -> ResultT:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return await operation()
        except Exception as exc:
            if not isinstance(exc, retryable_exceptions):
                raise
            last_error = exc
            if attempt >= retries:
                break
            delay = min(base_delay_seconds * (2 ** (attempt - 1)), max_delay_seconds)
            await asyncio.sleep(delay)

    assert last_error is not None
    raise last_error
