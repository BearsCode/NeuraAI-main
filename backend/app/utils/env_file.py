from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True, slots=True)
class EnvDiscoveryLayout:
    """Declarative layout for resolving category-based dotenv files."""

    root_markers: tuple[str, ...] = ("pyproject.toml", ".git", "docker-compose.yml")
    base_env_dir: str = "config/env"
    shared_subdir: str = "base"
    default_profile: str = "local"
    override_files: tuple[str, ...] = (".env", ".env.local")
    env_suffix: str = ".env"


class EnvFilesResolver:
    """Resolves the ordered list of dotenv files used by the backend runtime."""

    def __init__(self, *, start_path: Path | None = None, layout: EnvDiscoveryLayout | None = None) -> None:
        self.start_path = start_path or Path(__file__).resolve().parent
        self.layout = layout or EnvDiscoveryLayout()

    def resolve(self) -> tuple[Path, ...]:
        project_root = self._find_project_root()
        files: list[Path] = []

        files.extend(self._resolve_directory_files(project_root / self.layout.base_env_dir / self.layout.shared_subdir))
        files.extend(self._resolve_directory_files(project_root / self.layout.base_env_dir / self._resolve_profile()))
        files.extend(self._resolve_override_files(project_root))

        seen: set[Path] = set()
        ordered: list[Path] = []
        for file_path in files:
            resolved = file_path.resolve()
            if resolved in seen or not resolved.is_file():
                continue
            seen.add(resolved)
            ordered.append(resolved)
        return tuple(ordered)

    def _find_project_root(self) -> Path:
        current_path = self.start_path
        while current_path != current_path.parent:
            if any((current_path / marker).exists() for marker in self.layout.root_markers):
                return current_path
            current_path = current_path.parent
        return self.start_path

    def _resolve_profile(self) -> str:
        raw_profile = (
            os.getenv("NEURA_ENV_PROFILE")
            or os.getenv("APP__ENV")
            or os.getenv("APP_ENV")
            or self.layout.default_profile
        )
        profile = str(raw_profile).strip().lower()
        return profile or self.layout.default_profile

    def _resolve_directory_files(self, directory: Path) -> list[Path]:
        if not directory.is_dir():
            return []
        return sorted(
            (
                path
                for path in directory.glob(f"*{self.layout.env_suffix}")
                if path.is_file()
            ),
            key=_env_file_sort_key,
        )

    def _resolve_override_files(self, project_root: Path) -> list[Path]:
        override_files = _parse_path_list(os.getenv("NEURA_ENV_FILES")) or self.layout.override_files
        resolved: list[Path] = []
        for item in override_files:
            path = Path(item)
            resolved.append(path if path.is_absolute() else project_root / path)
        return resolved


def _parse_path_list(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _env_file_sort_key(path: Path) -> tuple[int, str]:
    match = re.match(r"(?P<prefix>\d+)[-_]", path.name)
    if not match:
        return (10_000, path.name)
    return (int(match.group("prefix")), path.name)


def get_env_files() -> tuple[Path, ...]:
    return EnvFilesResolver().resolve()


def get_env() -> Path | tuple[Path, ...] | None:
    files = get_env_files()
    if not files:
        return None
    return files if len(files) > 1 else files[0]


env_files = get_env_files()
env_file = env_files if env_files else None
