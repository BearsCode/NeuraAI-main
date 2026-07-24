from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import dotenv_values
from pydantic_settings.sources import PydanticBaseSettingsSource

from backend.app.core.configs.sources.mappings import LEGACY_ENV_MAPPINGS, LegacyEnvMapping, ai_provider_env_mappings
from backend.app.core.configs.normalizers import normalize_ai_provider


class LegacyEnvSettingsSource(PydanticBaseSettingsSource):
    """Maps legacy flat env vars into the structured settings model."""

    def __init__(
        self,
        settings_cls,
        *,
        env_file: str | os.PathLike[str] | tuple[str | os.PathLike[str], ...] | list[str | os.PathLike[str]] | None,
        env_file_encoding: str | None,
    ) -> None:
        super().__init__(settings_cls)
        self.env_file = env_file
        self.env_file_encoding = env_file_encoding

    def get_field_value(self, field, field_name: str) -> tuple[Any, str, bool]:
        return None, field_name, False

    def __call__(self) -> dict[str, Any]:
        raw = _load_raw_env(self.env_file, self.env_file_encoding)
        payload: dict[str, Any] = {}

        _apply_mappings(payload, raw, LEGACY_ENV_MAPPINGS)

        provider = _normalize_provider(raw.get("AI_PROVIDER"))
        _set(payload, ("ai", "provider"), provider)
        if provider in {"openai", "claude", "gemini"}:
            _apply_mappings(payload, raw, ai_provider_env_mappings(provider))

        return payload


def _load_raw_env(
    env_file: str | os.PathLike[str] | tuple[str | os.PathLike[str], ...] | list[str | os.PathLike[str]] | None,
    env_file_encoding: str | None,
) -> dict[str, str]:
    raw: dict[str, str] = {}
    for file_path in _iter_env_files(env_file):
        path = Path(file_path)
        if not path.is_file():
            continue
        raw.update(
            {
                key: value
                for key, value in dotenv_values(path, encoding=env_file_encoding).items()
                if value is not None
            }
        )
    raw.update(os.environ)
    return raw


def _iter_env_files(
    env_file: str | os.PathLike[str] | tuple[str | os.PathLike[str], ...] | list[str | os.PathLike[str]] | None,
) -> tuple[str | os.PathLike[str], ...]:
    if env_file is None:
        return ()
    if isinstance(env_file, (str, os.PathLike)):
        return (env_file,)
    return tuple(env_file)


def _apply_mappings(payload: dict[str, Any], raw: dict[str, str], mappings: tuple[LegacyEnvMapping, ...]) -> None:
    for mapping in mappings:
        for key in mapping.keys:
            value = raw.get(key)
            if value is None or value == "":
                continue
            _set(payload, mapping.path, value)
            break


def _normalize_provider(value: str | None) -> str:
    normalized = normalize_ai_provider(value)
    if not isinstance(normalized, str):
        return "mock"
    return normalized


def _set(payload: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    if value is None or value == "":
        return
    current = payload
    for key in path[:-1]:
        current = current.setdefault(key, {})
    current[path[-1]] = value
