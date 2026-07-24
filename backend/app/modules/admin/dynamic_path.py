from __future__ import annotations

import hashlib
import hmac
import time
from datetime import UTC, date, datetime, timedelta

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.core.configs import settings

DECOY_PATHS = {"/admin", "/administrator", "/dashboard", "/admin/", "/administrator/", "/dashboard/"}


def _generate_path_for_date(target_date: date) -> str:
    key = settings.admin.admin_secret_key.get_secret_value().encode("utf-8")
    salt = settings.admin.admin_salt.encode("utf-8")
    date_str = target_date.isoformat()
    msg = f"{date_str}:{salt.decode()}".encode("utf-8")
    digest = hmac.new(key, msg, hashlib.sha256).hexdigest()[:12]
    path = f"/{digest}-admin"
    return path


def get_today_path() -> str:
    return _generate_path_for_date(date.today())


def get_login_path() -> str:
    return get_today_path().replace("-admin", "-admin-login")


def get_yesterday_path() -> str:
    yesterday = date.today() - timedelta(days=1)
    return _generate_path_for_date(yesterday)


def get_valid_paths() -> list[str]:
    paths = [get_today_path()]
    grace = settings.admin.admin_path_grace_hours
    if grace > 0:
        paths.append(get_yesterday_path())
    return paths


def is_valid_admin_path(path: str) -> bool:
    return path in get_valid_paths()


def generate_emergency_path(ip_address: str) -> tuple[str, datetime]:
    ts = int(time.time() / 1800)
    key = settings.admin.admin_secret_key.get_secret_value().encode("utf-8")
    salt = settings.admin.admin_salt.encode("utf-8")
    msg = f"emergency:{ip_address}:{ts}:{salt.decode()}".encode("utf-8")
    digest = hmac.new(key, msg, hashlib.sha256).hexdigest()[:12]
    path = f"/{digest}-emergency"
    expires_at = datetime.now(UTC) + timedelta(minutes=30)
    return path, expires_at


class AdminPathMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path.rstrip("/") or "/"
        clean_path = path

        valid_paths = get_valid_paths()
        is_admin_request = clean_path in valid_paths or any(clean_path.startswith(p + "/") for p in valid_paths)

        if clean_path in DECOY_PATHS:
            return Response(status_code=404)

        if is_admin_request:
            request.state.is_admin_request = True
        else:
            request.state.is_admin_request = False

        response = await call_next(request)
        return response
