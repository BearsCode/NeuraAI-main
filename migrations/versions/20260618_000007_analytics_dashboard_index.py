"""analytics dashboard index

Revision ID: 20260618_000007
Revises: 20260618_000006
Create Date: 2026-06-18 16:40:00
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import inspect

revision = "20260618_000007"
down_revision = "20260618_000006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("analytics_snapshots"):
        return
    existing = {item["name"] for item in inspector.get_indexes("analytics_snapshots")}
    if "ix_analytics_snapshots_project_platform_collected" not in existing:
        op.create_index(
            "ix_analytics_snapshots_project_platform_collected",
            "analytics_snapshots",
            ["tenant_id", "project_id", "platform", "collected_at"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("analytics_snapshots"):
        return
    existing = {item["name"] for item in inspector.get_indexes("analytics_snapshots")}
    if "ix_analytics_snapshots_project_platform_collected" in existing:
        op.drop_index("ix_analytics_snapshots_project_platform_collected", table_name="analytics_snapshots")
