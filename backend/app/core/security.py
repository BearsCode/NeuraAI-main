from __future__ import annotations

import base64
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any, Literal
from uuid import uuid4

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.exc import UnknownHashError

from backend.app.core.configs import settings

ALGORITHM = "HS256"
PASSWORD_CONTEXT = CryptContext(schemes=["argon2"], deprecated="auto")


@dataclass(slots=True)
class TokenPayload:
    subject: str
    token_type: Literal["access", "refresh"]
    expires_at: datetime
    role: str | None = None
    token_id: str | None = None
    tenant_id: str | None = None


def get_password_hash(password: str) -> str:
    return PASSWORD_CONTEXT.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return PASSWORD_CONTEXT.verify(plain_password, hashed_password)
    except UnknownHashError:
        return False


def is_password_hash_supported(hashed_password: str) -> bool:
    try:
        return PASSWORD_CONTEXT.identify(hashed_password) is not None
    except UnknownHashError:
        return False


def create_access_token(subject: str, role: str, tenant_id: str | None = None) -> tuple[str, int]:
    expires_delta = timedelta(minutes=settings.security.access_token_ttl_minutes)
    expire_at = datetime.now(UTC) + expires_delta
    payload = _build_token_payload(
        subject=subject,
        token_type="access",
        expires_at=expire_at,
        role=role,
        tenant_id=tenant_id,
    )
    token = jwt.encode(payload, settings.security.jwt_secret_key.get_secret_value(), algorithm=ALGORITHM)
    return token, int(expires_delta.total_seconds())


def create_refresh_token(subject: str) -> tuple[str, str, int, datetime]:
    expires_delta = timedelta(days=settings.security.refresh_token_ttl_days)
    expire_at = datetime.now(UTC) + expires_delta
    token_id = uuid4().hex
    payload = _build_token_payload(
        subject=subject,
        token_type="refresh",
        expires_at=expire_at,
        token_id=token_id,
    )
    token = jwt.encode(payload, settings.security.jwt_secret_key.get_secret_value(), algorithm=ALGORITHM)
    return token, token_id, int(expires_delta.total_seconds()), expire_at


def decode_access_token(token: str) -> TokenPayload:
    return decode_token(token, expected_type="access")


def decode_refresh_token(token: str) -> TokenPayload:
    return decode_token(token, expected_type="refresh")


def decode_token(
    token: str,
    expected_type: Literal["access", "refresh"] | None = None,
) -> TokenPayload:
    payload = jwt.decode(
        token,
        settings.security.jwt_secret_key.get_secret_value(),
        algorithms=[ALGORITHM],
        audience=settings.security.jwt_audience,
        issuer=settings.security.jwt_issuer,
    )

    token_type = payload.get("type")
    if expected_type and token_type != expected_type:
        raise JWTError("Invalid token type")

    subject = payload.get("sub")
    if not subject:
        raise JWTError("Missing token subject")

    return TokenPayload(
        subject=subject,
        token_type=token_type,
        expires_at=_normalize_datetime(payload.get("exp")),
        role=payload.get("role"),
        token_id=payload.get("jti"),
        tenant_id=payload.get("tenant_id"),
    )


def hash_token_id(token_id: str) -> str:
    return sha256(token_id.encode("utf-8")).hexdigest()


def is_jwt_error(error: Exception) -> bool:
    return isinstance(error, JWTError)


def _transliterate(text: str) -> str:
    mapping = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
        "ж": "zh", "з": "z", "и": "i", "й": "i", "к": "k", "л": "l", "м": "m",
        "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
        "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
        "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "iu", "я": "ia",
    }
    return "".join(mapping.get(c, c) for c in text)


def generate_referral_code(seed: str) -> str:
    latin = _transliterate(seed.lower())
    sanitized = "".join(char for char in latin if char.isalnum())[:8]
    prefix = sanitized or "neura"
    return f"{prefix}-{uuid4().hex[:6]}"


def generate_numeric_otp(length: int = 6) -> str:
    """Return a cryptographically secure numeric OTP."""

    return f"{secrets.randbelow(10**length):0{length}d}"


def hash_email_otp(email: str, code: str) -> str:
    """Return a stable HMAC hash for an email confirmation code using dedicated OTP signing key."""

    from backend.app.core.configs import settings
    raw = settings.security.otp_signing_key.get_secret_value() if settings.security.otp_signing_key else ""
    key = raw.encode("utf-8")
    msg = f"{email.strip().lower()}:{code}".encode("utf-8")
    return hmac.new(key, msg, "sha256").hexdigest()


def encrypt_secret(value: str) -> str:
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str | None) -> str | None:
    if not value:
        return None
    return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")


def scrub_pii(payload: dict[str, Any]) -> dict[str, Any]:
    pii_keys = {"email", "phone", "access_token", "refresh_token", "password", "token"}
    return {
        key: ("***" if key in pii_keys else value)
        for key, value in payload.items()
    }


def _build_token_payload(
    *,
    subject: str,
    token_type: Literal["access", "refresh"],
    expires_at: datetime,
    role: str | None = None,
    token_id: str | None = None,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    issued_at = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": issued_at,
        "nbf": issued_at,
        "exp": expires_at,
        "iss": settings.security.jwt_issuer,
        "aud": settings.security.jwt_audience,
    }
    if role:
        payload["role"] = role
    if token_id:
        payload["jti"] = token_id
    if tenant_id:
        payload["tenant_id"] = tenant_id
    return payload


def _normalize_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(UTC)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=UTC)
    raise JWTError("Invalid exp payload")


_cached_fernet: Fernet | None = None


def _fernet() -> Fernet:
    global _cached_fernet
    if _cached_fernet is None:
        raw_secret = settings.security.token_encryption_key.get_secret_value().encode("utf-8")
        derived_key = base64.urlsafe_b64encode(sha256(raw_secret).digest())
        _cached_fernet = Fernet(derived_key)
    return _cached_fernet
