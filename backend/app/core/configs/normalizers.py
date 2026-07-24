from __future__ import annotations

import ipaddress
import json
from collections.abc import Iterable
import re
from urllib.parse import urlsplit


HOSTNAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.-]{0,253}[A-Za-z0-9]$")
REQUEST_HEADER_PATTERN = re.compile(r"^[A-Za-z0-9-]+$")
S3_BUCKET_PATTERN = re.compile(r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$")
QUEUE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9:_-]+$")
DATABASE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,62}$")


def normalize_optional_string(value: object) -> str | None:
    """Strip whitespace and collapse empty values to None."""
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    stripped = str(value).strip()
    return stripped or None


def normalize_string(value: object) -> str | object:
    """Strip whitespace from a required string value."""
    if not isinstance(value, str):
        return value
    return value.strip()


def normalize_optional_url(value: object) -> str | None:
    """Normalize optional URL-like values by trimming and removing trailing slash."""
    normalized = normalize_optional_string(value)
    return normalized.rstrip("/") if normalized else None


def normalize_url(value: object) -> str | object:
    """Normalize required URL-like values by trimming and removing trailing slash."""
    if not isinstance(value, str):
        return value
    return value.strip().rstrip("/")


def ensure_leading_slash(value: object) -> str | object:
    """Ensure API prefixes and webhook paths always start with a slash."""
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not stripped:
        return stripped
    return stripped if stripped.startswith("/") else f"/{stripped}"


def normalize_string_list(value: object) -> list[str] | object:
    """Accept JSON arrays, CSV strings, or iterables for list[str] fields."""
    if value in (None, "", []):
        return []

    items: Iterable[object]
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith("["):
            parsed = json.loads(stripped)
            items = parsed if isinstance(parsed, list) else [parsed]
        else:
            items = stripped.split(",")
    elif isinstance(value, (list, tuple, set)):
        items = value
    else:
        return value

    normalized: list[str] = []
    seen: set[str] = set()
    for item in items:
        current = normalize_optional_string(item)
        if current is None or current in seen:
            continue
        normalized.append(current)
        seen.add(current)
    return normalized


def normalize_int_list(value: object) -> list[int] | object:
    """Accept JSON arrays, CSV strings, or iterables for list[int] fields."""
    if value in (None, "", []):
        return []

    items: Iterable[object]
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith("["):
            parsed = json.loads(stripped)
            items = parsed if isinstance(parsed, list) else [parsed]
        else:
            items = stripped.split(",")
    elif isinstance(value, (list, tuple, set)):
        items = value
    else:
        return value

    normalized: list[int] = []
    seen: set[int] = set()
    for item in items:
        current = normalize_optional_string(item)
        if current is None:
            continue
        parsed = int(current)
        if parsed in seen:
            continue
        normalized.append(parsed)
        seen.add(parsed)
    return normalized


def normalize_log_level(value: object) -> str | object:
    """Normalize common log level aliases to stdlib-compatible names."""
    normalized = normalize_optional_string(value)
    if normalized is None:
        return value
    mapping = {
        "WARN": "WARNING",
        "FATAL": "CRITICAL",
    }
    return mapping.get(normalized.upper(), normalized.upper())


def normalize_ai_provider(value: object) -> str | object:
    """Normalize provider aliases to internal provider identifiers."""
    normalized = normalize_optional_string(value)
    if normalized is None:
        return value
    aliases = {
        "anthropic": "claude",
        "stub": "mock",
    }
    return aliases.get(normalized.lower(), normalized.lower())



def normalize_database_dsn(value: object) -> str | None:
    """Normalize DB DSNs and upgrade plain postgres schemes to asyncpg."""
    normalized = normalize_optional_string(value)
    if normalized is None:
        return None
    if normalized.startswith("postgres://"):
        return normalized.replace("postgres://", "postgresql+asyncpg://", 1)
    if normalized.startswith("postgresql://"):
        return normalized.replace("postgresql://", "postgresql+asyncpg://", 1)
    return normalized


def validate_hostname_or_ip(value: str, *, field_name: str) -> str:
    """Validate host-like values used by network clients."""
    normalized = value.strip()
    try:
        ipaddress.ip_address(normalized)
        return normalized
    except ValueError:
        if HOSTNAME_PATTERN.fullmatch(normalized):
            return normalized
    raise ValueError(f"{field_name} must be a valid hostname or IP address")


def validate_request_header_name(value: str) -> str:
    """Validate a custom HTTP header name."""
    normalized = value.strip()
    if not REQUEST_HEADER_PATTERN.fullmatch(normalized):
        raise ValueError("request_id_header must contain only letters, digits, and hyphens")
    return normalized


def validate_s3_bucket_name(value: str) -> str:
    """Validate an S3-compatible bucket name."""
    normalized = value.strip().lower()
    if not S3_BUCKET_PATTERN.fullmatch(normalized):
        raise ValueError("bucket must be a valid S3 bucket name")
    if ".." in normalized or ".-" in normalized or "-." in normalized:
        raise ValueError("bucket must not contain adjacent dots or dot-hyphen sequences")
    try:
        ipaddress.ip_address(normalized)
    except ValueError:
        return normalized
    raise ValueError("bucket must not be formatted as an IP address")


def validate_queue_name(value: str) -> str:
    """Validate Redis queue and stream names."""
    normalized = value.strip()
    if not QUEUE_NAME_PATTERN.fullmatch(normalized):
        raise ValueError("queue names may contain only letters, digits, colon, underscore, and hyphen")
    return normalized


def validate_database_name(value: str) -> str:
    """Validate a database name when DSN is assembled from discrete fields."""
    normalized = value.strip()
    if not DATABASE_NAME_PATTERN.fullmatch(normalized):
        raise ValueError("database must contain only letters, digits, underscores, or hyphens")
    return normalized


def validate_absolute_url(value: str, *, field_name: str, allowed_schemes: tuple[str, ...]) -> str:
    """Ensure URLs are absolute and use an allowed scheme."""
    normalized = normalize_url(value)
    if not isinstance(normalized, str) or not normalized:
        raise ValueError(f"{field_name} must be a non-empty absolute URL")

    parsed = urlsplit(normalized)
    if parsed.scheme not in allowed_schemes or not parsed.netloc:
        allowed = ", ".join(allowed_schemes)
        raise ValueError(f"{field_name} must use one of: {allowed}")
    return normalized
