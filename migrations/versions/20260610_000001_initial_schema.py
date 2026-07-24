"""initial schema

Revision ID: 20260610_000001
Revises: None
Create Date: 2026-06-10 16:45:00
"""

from datetime import date

from alembic import op

from backend.app.db import Base
from backend.app.db import models 

revision = "20260610_000001"
down_revision = None
branch_labels = None
depends_on = None

TENANT_TIME_PARTITIONED_TABLES = (
    "analytics_snapshots",
    "audit_logs",
    "outbox_events",
)
PARTITION_START = date(2026, 1, 1)
PARTITION_MONTHS_AHEAD = 24
TENANT_HASH_PARTITIONS = 8


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)
    if bind.dialect.name == "postgresql":
        _create_tenant_time_partitions()
        _create_search_indexes()


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        _drop_tenant_time_partitions()
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)


def _create_tenant_time_partitions() -> None:
    for table_name in TENANT_TIME_PARTITIONED_TABLES:
        _create_tenant_hash_subpartitions(f"{table_name}_default", table_name, "DEFAULT")
        current = PARTITION_START
        for _ in range(PARTITION_MONTHS_AHEAD):
            next_month = _add_month(current)
            partition_name = f"{table_name}_{current.year}_{current.month:02d}"
            op.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {partition_name}
                PARTITION OF {table_name}
                FOR VALUES FROM ('{current.isoformat()}') TO ('{next_month.isoformat()}')
                PARTITION BY HASH (tenant_id)
                """
            )
            for remainder in range(TENANT_HASH_PARTITIONS):
                op.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {partition_name}_h{remainder}
                    PARTITION OF {partition_name}
                    FOR VALUES WITH (MODULUS {TENANT_HASH_PARTITIONS}, REMAINDER {remainder})
                    """
                )
            current = next_month


def _create_tenant_hash_subpartitions(partition_name: str, table_name: str, bounds: str) -> None:
    op.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {partition_name}
        PARTITION OF {table_name}
        {bounds}
        PARTITION BY HASH (tenant_id)
        """
    )
    for remainder in range(TENANT_HASH_PARTITIONS):
        op.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {partition_name}_h{remainder}
            PARTITION OF {partition_name}
            FOR VALUES WITH (MODULUS {TENANT_HASH_PARTITIONS}, REMAINDER {remainder})
            """
        )


def _add_month(value: date) -> date:
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def _create_search_indexes() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_tenants_search_document_fts
        ON tenants
        USING GIN (to_tsvector('simple', search_document))
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_projects_search_document_fts
        ON projects
        USING GIN (to_tsvector('simple', search_document))
        """
    )


def _drop_tenant_time_partitions() -> None:
    for table_name in TENANT_TIME_PARTITIONED_TABLES:
        op.execute(f"DROP TABLE IF EXISTS {table_name}_default CASCADE")
        current = PARTITION_START
        for _ in range(PARTITION_MONTHS_AHEAD):
            op.execute(f"DROP TABLE IF EXISTS {table_name}_{current.year}_{current.month:02d} CASCADE")
            current = _add_month(current)
