from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Generic, TypeVar


ResultT = TypeVar("ResultT")


@dataclass
class CircuitState:
    failures: int = 0
    opened_until: datetime | None = None


class CircuitBreaker(Generic[ResultT]):
    """Simple async circuit breaker suitable for external API adapters."""

    def __init__(self, failure_threshold: int, reset_timeout_seconds: int) -> None:
        self.failure_threshold = failure_threshold
        self.reset_timeout_seconds = reset_timeout_seconds
        self.state = CircuitState()

    async def call(self, operation: Callable[[], Awaitable[ResultT]]) -> ResultT:
        now = datetime.now(UTC)
        if self.state.opened_until and self.state.opened_until > now:
            raise RuntimeError("Circuit breaker is open")

        try:
            result = await operation()
        except Exception:
            self.state.failures += 1
            if self.state.failures >= self.failure_threshold:
                self.state.opened_until = now + timedelta(seconds=self.reset_timeout_seconds)
            raise

        self.state.failures = 0
        self.state.opened_until = None
        return result
