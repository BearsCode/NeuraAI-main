"""mini plan onboarding extensions

Revision ID: 20260613_000003
Revises: 20260613_000002
Create Date: 2026-06-13 21:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy import inspect

from backend.app.db import Base
from backend.app.db import models  # noqa: F401

revision = "20260613_000003"
down_revision = "20260613_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if context.is_offline_mode():
        return
    Base.metadata.create_all(bind=bind)
    inspector = inspect(bind)
    _add_column_if_missing(inspector, "projects", sa.Column("company_inn", sa.String(32), nullable=True))
    _add_column_if_missing(inspector, "projects", sa.Column("offer_accepted_at", sa.DateTime(timezone=True), nullable=True))
    _add_column_if_missing(inspector, "projects", sa.Column("data_confirmed_at", sa.DateTime(timezone=True), nullable=True))
    _add_column_if_missing(inspector, "projects", sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    return None


def _add_column_if_missing(inspector, table_name: str, column: sa.Column) -> None:
    if not inspector.has_table(table_name):
        return
    existing = {item["name"] for item in inspector.get_columns(table_name)}
    if column.name in existing:
        return
    op.add_column(table_name, column)
