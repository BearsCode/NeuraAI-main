"""publication history and notifications

Revision ID: 20260618_000006
Revises: 20260618_000005
Create Date: 2026-06-18 15:10:00
"""

from __future__ import annotations

from alembic import context, op

from backend.app.db import Base
from backend.app.db import models  # noqa: F401

revision = "20260618_000006"
down_revision = "20260618_000005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if context.is_offline_mode():
        return
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    return None
