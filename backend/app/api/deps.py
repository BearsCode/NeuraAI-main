from __future__ import annotations

from collections.abc import Awaitable, Callable
from functools import lru_cache
from typing import TypeVar
from uuid import uuid4

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from pydantic import BaseModel
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db_session
from backend.app.core.security import decode_access_token
from backend.app.core.configs import settings
from backend.app.db.enums import AdminRole, UserRole
from backend.app.db.subscription import Subscription
from backend.app.db.user import User
from backend.app.integrations.ai_client import AIClient
from backend.app.integrations.queue_client import QueueClient
from backend.app.integrations.storage_client import StorageClient
from backend.app.infra.idempotency import IdempotencyContext, IdempotencyService
from backend.app.infra.rate_limit import RateLimitContext, RateLimiter
from backend.app.observability.logging import get_logger

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.web.api_v1_prefix}/identity/token",
    auto_error=False,
)
ModelT = TypeVar("ModelT", bound=BaseModel)


def get_request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


@lru_cache(maxsize=1)
def get_ai_client() -> AIClient:
    return AIClient()


@lru_cache(maxsize=1)
def get_queue_client() -> QueueClient:
    return QueueClient()


@lru_cache(maxsize=1)
def get_storage_client() -> StorageClient:
    return StorageClient()


async def get_optional_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> User | None:
    cached = getattr(request.state, "current_user", None)
    if cached is not None:
        return cached
    if not token:
        token = request.cookies.get("neura_access_token")
    if not token:
        return None

    try:
        payload = decode_access_token(token)
        user_id = payload.subject
        if not user_id:
            return None
    except JWTError:
        return None
    except Exception as error:
        logger.error("unexpected_auth_error", extra={"error": str(error), "error_type": type(error).__name__})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal authentication error",
        ) from error

    auth_context = getattr(request.state, "auth_context", None)
    if auth_context is not None:
        request.state.current_tenant_id = auth_context.tenant_id
        request.state.current_project_id = auth_context.project_id

    user = await session.scalar(select(User).where(User.id == user_id))
    if not user or not user.is_active:
        return None

    request.state.current_user = user
    return user


async def get_current_user(
    current_user: User | None = Depends(get_optional_current_user),
) -> User:
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


def require_roles(*roles: UserRole) -> Callable[[User], Awaitable[User]]:
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return dependency


async def require_idempotency_header(
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> str:
    if not idempotency_key and _should_autogenerate_idempotency_key(request):
        idempotency_key = uuid4().hex
        request.state.generated_idempotency_key = idempotency_key

    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required",
        )
    return idempotency_key


async def enforce_rate_limit(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> None:
    limiter = RateLimiter(request.app.state.redis)
    limit, window_seconds = await _resolve_rate_limit(
        session=session,
        path=request.url.path,
        method=request.method,
        current_user=current_user,
        tenant_id=request.headers.get("X-Tenant-ID"),
    )
    actor_key = current_user.id if current_user else f"anon:{request.client.host if request.client else 'unknown'}"

    try:
        await limiter.enforce(
            RateLimitContext(
                actor_key=actor_key,
                endpoint=request.url.path,
                limit=limit,
                window_seconds=window_seconds,
            )
        )
    except RedisError:
        logger.warning("rate_limiter_disabled", extra={"reason": "redis_unavailable"})
        return


async def execute_idempotent(
    *,
    request: Request,
    session: AsyncSession,
    current_user: User,
    tenant_id: str,
    idempotency_key: str,
    payload: BaseModel,
    response_model: type[ModelT],
    operation: Callable[[], Awaitable[ModelT]],
) -> ModelT:
    result = await IdempotencyService().execute(
        session=session,
        context=IdempotencyContext(
            tenant_id=tenant_id,
            user_id=current_user.id,
            endpoint=request.url.path,
            key=idempotency_key,
            request_body=payload.model_dump(mode="json"),
        ),
        operation=operation,
        serializer=lambda item: item.model_dump(mode="json"),
        deserializer=response_model.model_validate,
    )
    return result.value


async def _resolve_rate_limit(
    *,
    session: AsyncSession,
    path: str,
    method: str,
    current_user: User | None,
    tenant_id: str | None,
) -> tuple[int, int]:
    if current_user is None:
        return settings.rate_limit.anonymous_requests_per_minute, settings.redis.rate_limit_ttl_seconds

    base_limit = settings.rate_limit.client_requests_per_minute
    if current_user.role == UserRole.PARTNER:
        base_limit = settings.rate_limit.partner_requests_per_minute
    elif current_user.role == UserRole.ADMIN:
        base_limit = settings.rate_limit.admin_requests_per_minute

    if method in {"POST", "PATCH"} and "/publishing/" in path:
        return await _limit_for_subscription(
            session=session,
            tenant_id=tenant_id,
            default_limit=min(base_limit, settings.rate_limit.publish_per_hour),
            quota_field="publications_per_hour",
        )

    if method == "POST" and (
        "/content-plans/" in path or path.endswith("/ai-analysis") or "/ai-optimization/" in path
    ):
        return await _limit_for_subscription(
            session=session,
            tenant_id=tenant_id,
            default_limit=min(base_limit, settings.rate_limit.generation_per_hour),
            quota_field="content_generations_per_hour",
        )

    return base_limit, settings.redis.rate_limit_ttl_seconds


async def _limit_for_subscription(
    *,
    session: AsyncSession,
    tenant_id: str | None,
    default_limit: int,
    quota_field: str,
) -> tuple[int, int]:
    if not tenant_id:
        return default_limit, 3600

    subscription = await session.scalar(
        select(Subscription)
        .options(selectinload(Subscription.plan))
        .where(Subscription.tenant_id == tenant_id)
        .order_by(Subscription.created_at.desc())
    )
    if not subscription or not subscription.plan:
        return default_limit, 3600

    return int(min(default_limit, getattr(subscription.plan, quota_field))), 3600


def _should_autogenerate_idempotency_key(request: Request) -> bool:
    if settings.app.env != "local":
        return False

    referer = request.headers.get("referer", "")
    return "/docs" in referer or "/redoc" in referer


def require_admin_role(*roles: AdminRole) -> Callable[[User], Awaitable[User]]:
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.admin_role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )
        if current_user.admin_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient admin role",
            )
        return current_user

    return dependency


async def require_super_admin_email(current_user: User = Depends(get_current_user)) -> User:
    if current_user.email not in settings.admin.super_admin_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )
    if current_user.admin_role is None:
        current_user.admin_role = AdminRole.SUPER_OWNER
    return current_user


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.admin_role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
