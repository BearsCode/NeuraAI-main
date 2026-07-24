from __future__ import annotations

import ipaddress
import secrets
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user, get_db_session
from backend.app.core.configs import settings
from backend.app.db.admin_session import AdminSession
from backend.app.db.enums import AdminRole
from backend.app.db.user import User
from backend.app.infra.rate_limit import RateLimitContext, RateLimiter

CONFIRM_PREFIX = "admin:confirm:"


def require_admin(*roles: AdminRole) -> Callable[[Request, AsyncSession, User], Awaitable[User]]:
    async def dependency(
        request: Request,
        session: AsyncSession = Depends(get_db_session),
        current_user: User = Depends(get_current_user),
    ) -> User:
        await check_admin_ip_allowlist(request)

        if current_user.admin_role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled",
            )
        if current_user.admin_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient admin role",
            )

        await _bind_admin_session(request, current_user, session)
        await _admin_rate_limit(request, current_user)

        return current_user

    return dependency


async def _bind_admin_session(
    request: Request,
    current_user: User,
    session: AsyncSession,
) -> None:
    current_ip = request.client.host if request.client else None
    current_ua = request.headers.get("User-Agent")
    now = datetime.now(UTC)

    result = await session.execute(
        select(AdminSession)
        .where(
            AdminSession.user_id == current_user.id,
            AdminSession.is_active.is_(True),
            AdminSession.expires_at > now,
            AdminSession.impersonating_user_id.is_(None),
        )
        .order_by(AdminSession.created_at.desc())
        .limit(1)
    )
    admin_session = result.scalar_one_or_none()

    if admin_session is None:
        expires_at = now.replace(hour=23, minute=59, second=59)
        if expires_at <= now:
            expires_at = now.replace(hour=23, minute=59, second=59) + timedelta(days=1)
        admin_session = AdminSession(
            user_id=current_user.id,
            admin_role=current_user.admin_role.value if current_user.admin_role else "admin",
            ip_address=current_ip,
            user_agent=current_ua,
            is_active=True,
            expires_at=expires_at,
            last_activity_at=now,
        )
        session.add(admin_session)
        await session.commit()
        return

    if admin_session.ip_address and current_ip and admin_session.ip_address != current_ip:
        admin_session.is_active = False
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="IP address changed. Admin session revoked for security.",
        )

    if admin_session.user_agent and current_ua and admin_session.user_agent != current_ua:
        admin_session.is_active = False
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User-Agent changed. Admin session revoked for security.",
        )

    if admin_session.expires_at <= now:
        admin_session.is_active = False
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin session expired. Please log in again.",
        )

    admin_session.last_activity_at = now
    await session.commit()


async def _admin_rate_limit(request: Request, current_user: User) -> None:
    redis: Redis | None = getattr(request.app.state, "redis", None)
    if redis is None:
        return

    actor_key = f"admin:{current_user.id}"

    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        limit = settings.admin.rate_limit_write_per_minute
    else:
        limit = settings.admin.rate_limit_read_per_minute

    limiter = RateLimiter(redis)
    await limiter.enforce(
        RateLimitContext(
            actor_key=actor_key,
            endpoint=request.url.path,
            limit=limit,
            window_seconds=60,
        )
    )


async def issue_confirmation_token(
    redis: Redis,
    user_id: str,
    action: str,
    *,
    ttl_seconds: int = 300,
) -> str:
    token = secrets.token_urlsafe(32)
    key = f"{CONFIRM_PREFIX}{user_id}:{action}"
    await redis.setex(key, ttl_seconds, token)
    return token


async def require_confirmation_token(
    request: Request,
    action: str,
    token: str,
    user_id: str,
) -> bool:
    redis: Redis | None = getattr(request.app.state, "redis", None)
    if redis is None:
        return True
    key = f"{CONFIRM_PREFIX}{user_id}:{action}"
    stored = await redis.get(key)
    if stored is None or stored.decode() != token:
        return False
    await redis.delete(key)
    return True


def require_confirm(action: str) -> Callable[[Request], Awaitable[None]]:
    async def dependency(request: Request) -> None:
        token = request.headers.get("X-Confirm-Token")
        if not token:
            raise HTTPException(
                status_code=status.HTTP_428_PRECONDITION_REQUIRED,
                detail="Confirmation token required. Obtain one via POST /admin/confirm.",
            )
        user: User | None = getattr(request.state, "current_user", None)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
        if not await require_confirmation_token(request, action, token, user.id):
            raise HTTPException(
                status_code=status.HTTP_428_PRECONDITION_REQUIRED,
                detail="Invalid or expired confirmation token.",
            )
    return dependency


async def check_admin_ip_allowlist(request: Request) -> None:
    if not settings.admin.ip_allowlist:
        return

    client_ip = request.client.host if request.client else None
    if client_ip is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not determine client IP",
        )

    allowed = [
        ipaddress.ip_network(cidr.strip())
        for cidr in settings.admin.ip_allowlist
        if cidr.strip()
    ]
    try:
        ip_addr = ipaddress.ip_address(client_ip)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid client IP",
        )

    if not any(ip_addr in network for network in allowed):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="IP address not allowed for admin access",
        )
