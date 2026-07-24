from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import Connection

revision: str = "20260707_000013"
down_revision: Union[str, None] = "20260707_000012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {c["name"] for c in inspector.get_columns("users")}

    for col_name, col_type in [
        ("vk_id", sa.String(64)),
        ("yandex_id", sa.String(64)),
        ("mailru_id", sa.String(64)),
    ]:
        if col_name not in columns:
            op.add_column("users", sa.Column(col_name, col_type, nullable=True))

    existing_indexes = {ix["name"] for ix in inspector.get_indexes("users")}
    for idx_name in ["ix_users_vk_id", "ix_users_yandex_id", "ix_users_mailru_id"]:
        if idx_name not in existing_indexes:
            name_prefix = idx_name.replace("ix_users_", "")
            col_lookup = {"ix_users_vk_id": "vk_id", "ix_users_yandex_id": "yandex_id", "ix_users_mailru_id": "mailru_id"}
            op.create_index(idx_name, "users", [col_lookup[idx_name]], unique=True)

    if "ix_users_google_id" in existing_indexes:
        op.drop_index("ix_users_google_id")

    if "google_id" in columns:
        op.drop_column("users", "google_id")


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {c["name"] for c in inspector.get_columns("users")}

    if "google_id" not in columns:
        op.add_column("users", sa.Column("google_id", sa.String(255), nullable=True))

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_indexes = {ix["name"] for ix in inspector.get_indexes("users")}
    if "ix_users_google_id" not in existing_indexes:
        op.create_index("ix_users_google_id", "users", ["google_id"], unique=True)

    for idx in ["ix_users_mailru_id", "ix_users_yandex_id", "ix_users_vk_id"]:
        try:
            op.drop_index(idx)
        except sa.exc.ProgrammingError:
            conn.rollback()

    for col in ["mailru_id", "yandex_id", "vk_id"]:
        if col in columns:
            op.drop_column("users", col)
