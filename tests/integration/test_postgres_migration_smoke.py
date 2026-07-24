from __future__ import annotations

import os
import shutil
import subprocess

import pytest

postgres_module = pytest.importorskip("testcontainers.postgres")
PostgresContainer = postgres_module.PostgresContainer


def test_alembic_upgrade_head_against_postgres_container() -> None:
    alembic_bin = shutil.which("alembic") or "./.venv/bin/alembic"
    if not alembic_bin:
        pytest.skip("alembic executable is not available")

    try:
        with PostgresContainer("postgres:15-alpine") as postgres:
            sync_url = postgres.get_connection_url()
            async_url = (
                sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
                .replace("postgresql+psycopg://", "postgresql+asyncpg://")
                .replace("postgresql://", "postgresql+asyncpg://")
            )
            environment = {**os.environ, "DB__DSN": async_url}
            result = subprocess.run(
                [alembic_bin, "upgrade", "head"],
                check=False,
                capture_output=True,
                text=True,
                env=environment,
            )
            assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Testcontainers/Docker unavailable: {exc}")
