import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.app.api.deps import require_idempotency_header


@pytest.mark.asyncio
async def test_require_idempotency_header_generates_for_local_docs_request() -> None:
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/content-plans/generate",
            "headers": [(b"referer", b"http://testserver/docs")],
        }
    )

    key = await require_idempotency_header(request, None)

    assert key
    assert request.state.generated_idempotency_key == key


@pytest.mark.asyncio
async def test_require_idempotency_header_still_fails_without_docs_referer() -> None:
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/content-plans/generate",
            "headers": [],
        }
    )

    with pytest.raises(HTTPException) as error:
        await require_idempotency_header(request, None)

    assert error.value.status_code == 400
    assert error.value.detail == "Idempotency-Key header is required"
