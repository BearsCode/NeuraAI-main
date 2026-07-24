from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260708_000014"
down_revision: Union[str, None] = "20260707_000013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "encrypted_permissions",
        type_=sa.Text(),
        existing_type=sa.String(1024),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "encrypted_permissions",
        type_=sa.String(1024),
        existing_type=sa.Text(),
        nullable=True,
    )
