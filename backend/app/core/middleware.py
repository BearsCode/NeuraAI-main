from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from uuid import uuid4

import structlog
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.app.core.database import database_manager
from backend.app.core.security import decode_access_token, is_jwt_error
from backend.app.core.configs import settings
from backend.app.db.user import User
from backend.app.observability.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class RequestAuthContext:
    """Authentication context propagated through the request lifecycle."""

    user_id: str | None = None
    role: str | None = None
    tenant_id: str | None = None
    project_id: str | None = None


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get(settings.web.request_id_header) or uuid4().hex
        request.state.request_id = request_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        started_at = perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = round((perf_counter() - started_at) * 1000, 2)
            logger.exception(
                "request_failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": request.client.host if request.client else None,
                    "elapsed_ms": elapsed_ms,
                },
            )
            structlog.contextvars.clear_contextvars()
            raise

        elapsed_ms = round((perf_counter() - started_at) * 1000, 2)
        logger.info(
            "request_completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
                "status_code": response.status_code,
                "elapsed_ms": elapsed_ms,
            },
        )
        structlog.contextvars.clear_contextvars()

        response.headers[settings.web.request_id_header] = request_id
        response.headers["X-Process-Time-Ms"] = str(elapsed_ms)
        generated_idempotency_key = getattr(request.state, "generated_idempotency_key", None)
        if generated_idempotency_key:
            response.headers["X-Generated-Idempotency-Key"] = generated_idempotency_key
        return response


class AuthenticationContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        token = _extract_bearer_token(request)
        tenant_id = request.headers.get("X-Tenant-ID")
        project_id = request.headers.get("X-Project-ID")
        request.state.auth_context = RequestAuthContext(tenant_id=tenant_id, project_id=project_id)

        if token:
            try:
                payload = decode_access_token(token)
                request.state.auth_context = RequestAuthContext(
                    user_id=payload.subject,
                    role=payload.role,
                    tenant_id=tenant_id or payload.tenant_id,
                    project_id=project_id,
                )
                async with database_manager.session_factory() as session:
                    user = await session.scalar(select(User).where(User.id == payload.subject))
                    if user and user.is_active:
                        request.state.current_user = user
            except Exception as error:  # noqa: BLE001
                if not is_jwt_error(error):
                    logger.warning("auth_context_middleware_error", extra={"error": str(error)})

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), camera=(), microphone=()")
        return response


def _extract_bearer_token(request: Request) -> str | None:
    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        return authorization[7:].strip()
    return request.cookies.get("neura_access_token")
