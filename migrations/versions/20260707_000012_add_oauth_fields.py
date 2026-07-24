from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260707_000012"
down_revision: Union[str, None] = "20260704_000011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {c["name"] for c in inspector.get_columns("users")}

    add_if_not_exists("google_id", sa.String(255), columns, conn, op)
    add_if_not_exists("telegram_id", sa.String(64), columns, conn, op)
    add_if_not_exists("vk_id", sa.String(64), columns, conn, op)
    add_if_not_exists("avatar_url", sa.String(512), columns, conn, op)

    existing_indexes = {ix["name"] for ix in inspector.get_indexes("users")}
    if "ix_users_google_id" not in existing_indexes:
        op.create_index("ix_users_google_id", "users", ["google_id"], unique=True)
    if "ix_users_telegram_id" not in existing_indexes:
        op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)
    if "ix_users_vk_id" not in existing_indexes:
        op.create_index("ix_users_vk_id", "users", ["vk_id"], unique=True)


def add_if_not_exists(
    col_name: str,
    col_type: sa.types.TypeEngine,
    existing: set[str],
    conn: sa.engine.Connection,
    op: op.Operations,
) -> None:
    if col_name not in existing:
        op.add_column("users", sa.Column(col_name, col_type, nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {c["name"] for c in inspector.get_columns("users")}

    for index in ["ix_users_vk_id", "ix_users_telegram_id", "ix_users_google_id"]:
        try:
            op.drop_index(index)
        except sa.exc.ProgrammingError:
            conn.rollback()

    for col in ["vk_id", "telegram_id", "google_id", "avatar_url"]:
        if col in columns:
            op.drop_column("users", col)
