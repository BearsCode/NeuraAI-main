"""add admin_role and encrypted_permissions to users

Revision ID: 20260702_000010
Revises: 7c5c99f59c26
Create Date: 2026-07-02 12:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op, context
from sqlalchemy import inspect

from backend.app.db import Base
from backend.app.db import models  # noqa: F401

revision = "20260702_000010"
down_revision = "7c5c99f59c26"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("users")}

    if "admin_role" not in columns:
        op.add_column(
            "users",
            sa.Column(
                "admin_role",
                sa.String(length=16),
                nullable=True,
            ),
        )
        op.create_index("ix_users_admin_role", "users", ["admin_role"])

    if "encrypted_permissions" not in columns:
        op.add_column(
            "users",
            sa.Column(
                "encrypted_permissions",
                sa.String(length=1024),
                nullable=True,
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("users")}

    if "encrypted_permissions" in columns:
        op.drop_column("users", "encrypted_permissions")
    if "admin_role" in columns:
        op.drop_index("ix_users_admin_role", table_name="users")
        op.drop_column("users", "admin_role")
