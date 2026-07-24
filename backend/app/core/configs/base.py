from __future__ import annotations

from functools import lru_cache
from typing import Any, TypeVar, cast

from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import PydanticBaseSettingsSource

from backend.app.core.configs.sources import LegacyEnvSettingsSource
from backend.app.utils.env_file import env_files


class ConfigSection(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        frozen=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class RootSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=env_files,
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type["RootSettings"],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        legacy_source = LegacyEnvSettingsSource(
            settings_cls,
            env_file=getattr(dotenv_settings, "env_file", None),
            env_file_encoding=getattr(dotenv_settings, "env_file_encoding", None),
        )
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            legacy_source,
            file_secret_settings,
        )


SectionType = TypeVar("SectionType", bound=ConfigSection)
_USE_DEFAULT_ENV = object()


@lru_cache(maxsize=None)
def _build_section_envelope(section_name: str, section_type: type[SectionType]) -> type[RootSettings]:
    namespace: dict[str, Any] = {
        "__module__": __name__,
        "__annotations__": {section_name: section_type},
        section_name: Field(default_factory=section_type),
    }
    return cast(type[RootSettings], type(f"{section_type.__name__}Envelope", (RootSettings,), namespace))


def load_section_settings(
    section_name: str,
    section_type: type[SectionType],
    *,
    env_file: Any = _USE_DEFAULT_ENV,
) -> SectionType:
    """Load a single configuration section from the shared env resolution pipeline."""

    envelope_cls = _build_section_envelope(section_name, section_type)
    init_kwargs: dict[str, Any] = {}
    if env_file is not _USE_DEFAULT_ENV:
        init_kwargs["_env_file"] = env_file
    envelope = envelope_cls(**init_kwargs)
    return cast(SectionType, getattr(envelope, section_name))
