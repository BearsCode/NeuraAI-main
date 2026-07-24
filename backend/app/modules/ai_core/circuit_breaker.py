from __future__ import annotations

import logging
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 1,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self._failures = 0
        self._state = "closed"
        self._last_failure_time = 0.0
        self._half_open_calls = 0

    @property
    def state(self) -> str:
        if self._state == "open" and (time.monotonic() - self._last_failure_time) >= self.recovery_timeout:
            self._state = "half-open"
            self._half_open_calls = 0
            logger.info("Circuit breaker %s: open -> half-open", self.name)
        return self._state

    def _trip(self) -> None:
        self._state = "open"
        self._last_failure_time = time.monotonic()
        logger.warning("Circuit breaker %s: closed -> open (threshold=%d)", self.name, self.failure_threshold)

    def _reset(self) -> None:
        self._state = "closed"
        self._failures = 0
        self._half_open_calls = 0
        logger.info("Circuit breaker %s: reset to closed", self.name)

    async def call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        current_state = self.state

        if current_state == "open":
            raise RuntimeError(f"Circuit breaker {self.name} is open")

        if current_state == "half-open":
            self._half_open_calls += 1
            if self._half_open_calls > self.half_open_max_calls:
                raise RuntimeError(f"Circuit breaker {self.name} half-open limit reached")

        try:
            result = await fn(*args, **kwargs)
            if current_state == "half-open":
                self._reset()
            return result
        except Exception:
            self._failures += 1
            if self._failures >= self.failure_threshold:
                self._trip()
            raise
