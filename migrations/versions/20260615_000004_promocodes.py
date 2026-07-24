"""promocode support

Revision ID: 20260615_000004
Revises: 20260613_000003
Create Date: 2026-06-15 13:40:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy import inspect

from backend.app.db import Base
from backend.app.db import models  # noqa: F401

revision = "20260615_000004"
down_revision = "20260613_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if context.is_offline_mode():
        return
    Base.metadata.create_all(bind=bind)
    inspector = inspect(bind)
    _add_column_if_missing(
        inspector,
        "subscriptions",
        sa.Column("active_promo_code_redemption_id", sa.String(36), nullable=True),
    )
    _create_index_if_missing(
        inspector,
        "subscriptions",
        "ix_subscriptions_active_promo_code_redemption_id",
        ["active_promo_code_redemption_id"],
    )


def downgrade() -> None:
    return None


def _add_column_if_missing(inspector, table_name: str, column: sa.Column) -> None:
    if not inspector.has_table(table_name):
        return
    existing = {item["name"] for item in inspector.get_columns(table_name)}
    if column.name in existing:
        return
    op.add_column(table_name, column)


def _create_index_if_missing(inspector, table_name: str, index_name: str, columns: list[str]) -> None:
    if not inspector.has_table(table_name):
        return
    existing = {item["name"] for item in inspector.get_indexes(table_name)}
    if index_name in existing:
        return
    op.create_index(index_name, table_name, columns)
