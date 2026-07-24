from __future__ import annotations

import httpx

from backend.app.workers.llm_worker import _is_retryable_ai_error


def _status_error(status_code: int) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://llm.example.com/generate")
    response = httpx.Response(status_code, request=request)
    return httpx.HTTPStatusError("LLM failed", request=request, response=response)


def test_retryable_ai_errors_cover_timeouts_rate_limits_and_server_errors() -> None:
    assert _is_retryable_ai_error(httpx.ReadTimeout("timeout"))
    assert _is_retryable_ai_error(TimeoutError("timeout"))
    assert _is_retryable_ai_error(_status_error(429))
    assert _is_retryable_ai_error(_status_error(503))
    assert _is_retryable_ai_error(RuntimeError("Circuit breaker is open"))


def test_retryable_ai_errors_reject_client_validation_errors() -> None:
    assert not _is_retryable_ai_error(_status_error(400))
    assert not _is_retryable_ai_error(ValueError("invalid JSON"))
