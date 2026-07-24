"""mvp compatibility schema bridge

Revision ID: 20260613_000002
Revises: 20260610_000001
Create Date: 2026-06-13 20:40:00
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy import inspect

from backend.app.db import Base
from backend.app.db import models  # noqa: F401

revision = "20260613_000002"
down_revision = "20260610_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if context.is_offline_mode():
        return
    Base.metadata.create_all(bind=bind)
    inspector = inspect(bind)
    _add_missing_columns(inspector)
    if bind.dialect.name == "sqlite":
        _backfill_sqlite_tenants(bind)


def downgrade() -> None:
    # Additive bridge migration. Downgrade intentionally keeps data and columns.
    return None


def _add_missing_columns(inspector) -> None:
    _add_column_if_missing(inspector, "users", sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
    _add_column_if_missing(inspector, "users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))

    for table_name in (
        "analytics_snapshots",
        "assets",
        "content_items",
        "content_plans",
        "project_strategies",
        "projects",
        "publications",
        "refresh_token_sessions",
        "social_integrations",
        "subscriptions",
    ):
        _add_column_if_missing(inspector, table_name, sa.Column("tenant_id", sa.String(36), nullable=True))

    _add_column_if_missing(inspector, "analytics_snapshots", sa.Column("platform", sa.String(64), nullable=False, server_default="all"))
    _add_column_if_missing(inspector, "analytics_snapshots", sa.Column("collected_at", sa.DateTime(timezone=True), nullable=True))
    _add_column_if_missing(inspector, "analytics_snapshots", sa.Column("raw_metrics", sa.JSON(), nullable=True))

    _add_column_if_missing(inspector, "assets", sa.Column("checksum_sha256", sa.String(64), nullable=True))
    _add_column_if_missing(inspector, "assets", sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"))

    _add_column_if_missing(inspector, "content_items", sa.Column("title", sa.String(255), nullable=True))
    _add_column_if_missing(inspector, "content_items", sa.Column("metadata_json", sa.JSON(), nullable=True))
    _add_column_if_missing(inspector, "content_items", sa.Column("current_version_number", sa.Integer(), nullable=False, server_default="1"))

    _add_column_if_missing(inspector, "content_plans", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    _add_column_if_missing(inspector, "projects", sa.Column("search_document", sa.Text(), nullable=False, server_default=""))

    _add_column_if_missing(inspector, "publications", sa.Column("all_or_nothing", sa.Boolean(), nullable=False, server_default=sa.true()))
    _add_column_if_missing(inspector, "publications", sa.Column("approval_required", sa.Boolean(), nullable=False, server_default=sa.true()))
    _add_column_if_missing(inspector, "publications", sa.Column("last_error_message", sa.Text(), nullable=True))
    _add_column_if_missing(inspector, "publications", sa.Column("saga_id", sa.String(64), nullable=True))
    _add_column_if_missing(inspector, "publications", sa.Column("platform", sa.String(17), nullable=False, server_default="telegram"))
    _add_column_if_missing(inspector, "publications", sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"))

    _add_column_if_missing(inspector, "social_integrations", sa.Column("encrypted_access_token", sa.Text(), nullable=True))
    _add_column_if_missing(inspector, "social_integrations", sa.Column("encrypted_refresh_token", sa.Text(), nullable=True))
    _add_column_if_missing(inspector, "social_integrations", sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True))
    _add_column_if_missing(inspector, "social_integrations", sa.Column("scopes", sa.JSON(), nullable=True))

    _add_column_if_missing(inspector, "subscriptions", sa.Column("plan_id", sa.String(36), nullable=True))
    _add_column_if_missing(inspector, "subscriptions", sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True))
    _add_column_if_missing(inspector, "subscriptions", sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True))
    _add_column_if_missing(inspector, "subscriptions", sa.Column("seats", sa.Integer(), nullable=False, server_default="1"))
    _add_column_if_missing(inspector, "subscriptions", sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True))


def _add_column_if_missing(inspector, table_name: str, column: sa.Column) -> None:
    if not inspector.has_table(table_name):
        return
    existing = {item["name"] for item in inspector.get_columns(table_name)}
    if column.name in existing:
        return
    op.add_column(table_name, column)


def _backfill_sqlite_tenants(bind) -> None:
    now = datetime.now(UTC).replace(tzinfo=None)
    projects = bind.execute(
        sa.text(
            """
            SELECT id, owner_user_id, company_name, city, industry
            FROM projects
            WHERE tenant_id IS NULL OR tenant_id = ''
            """
        )
    ).mappings()

    owner_to_tenant: dict[str, str] = {}
    for project in projects:
        owner_id = project["owner_user_id"]
        tenant_id = owner_to_tenant.get(owner_id)
        if tenant_id is None:
            tenant_id = uuid4().hex
            owner_to_tenant[owner_id] = tenant_id
            slug = f"legacy-{tenant_id[:12]}"
            bind.execute(
                sa.text(
                    """
                    INSERT INTO tenants
                    (id, slug, name, status, owner_user_id, default_timezone, industry, city, search_document, created_at, updated_at)
                    VALUES
                    (:id, :slug, :name, 'active', :owner_user_id, 'UTC', :industry, :city, :search_document, :created_at, :updated_at)
                    """
                ),
                {
                    "id": tenant_id,
                    "slug": slug,
                    "name": project["company_name"] or "Legacy Business",
                    "owner_user_id": owner_id,
                    "industry": project["industry"],
                    "city": project["city"],
                    "search_document": project["company_name"] or "",
                    "created_at": now,
                    "updated_at": now,
                },
            )
            bind.execute(
                sa.text(
                    """
                    INSERT INTO tenant_memberships
                    (id, tenant_id, user_id, role, is_primary, created_at, updated_at)
                    VALUES (:id, :tenant_id, :user_id, 'owner', 1, :created_at, :updated_at)
                    """
                ),
                {
                    "id": uuid4().hex,
                    "tenant_id": tenant_id,
                    "user_id": owner_id,
                    "created_at": now,
                    "updated_at": now,
                },
            )

        bind.execute(
            sa.text("UPDATE projects SET tenant_id = :tenant_id WHERE id = :project_id"),
            {"tenant_id": tenant_id, "project_id": project["id"]},
        )

    _backfill_tenant_from_project(bind, "assets", "project_id")
    _backfill_tenant_from_project(bind, "content_plans", "project_id")
    _backfill_tenant_from_project(bind, "content_items", "project_id")
    _backfill_tenant_from_project(bind, "project_strategies", "project_id")
    _backfill_tenant_from_project(bind, "publications", "project_id")
    _backfill_tenant_from_project(bind, "analytics_snapshots", "project_id")
    _backfill_tenant_from_project(bind, "social_integrations", "project_id")

    if _sqlite_has_column(bind, "subscriptions", "user_id"):
        starter_plan_id = _ensure_sqlite_starter_plan(bind, now)
        bind.execute(
            sa.text(
                """
                UPDATE subscriptions
                SET tenant_id = (
                    SELECT tm.tenant_id
                    FROM tenant_memberships tm
                    WHERE tm.user_id = subscriptions.user_id
                    ORDER BY tm.is_primary DESC
                    LIMIT 1
                ),
                plan_id = COALESCE(plan_id, :plan_id),
                starts_at = COALESCE(starts_at, created_at)
                WHERE tenant_id IS NULL OR tenant_id = ''
                """
            ),
            {"plan_id": starter_plan_id},
        )

    bind.execute(sa.text("UPDATE analytics_snapshots SET collected_at = COALESCE(collected_at, created_at)"))
    bind.execute(sa.text("UPDATE analytics_snapshots SET raw_metrics = COALESCE(raw_metrics, '{}')"))
    bind.execute(sa.text("UPDATE content_items SET metadata_json = COALESCE(metadata_json, '{}')"))
    bind.execute(sa.text("UPDATE social_integrations SET scopes = COALESCE(scopes, '[]')"))


def _backfill_tenant_from_project(bind, table_name: str, project_column: str) -> None:
    bind.execute(
        sa.text(
            f"""
            UPDATE {table_name}
            SET tenant_id = (
                SELECT projects.tenant_id
                FROM projects
                WHERE projects.id = {table_name}.{project_column}
            )
            WHERE tenant_id IS NULL OR tenant_id = ''
            """
        )
    )


def _ensure_sqlite_starter_plan(bind, now: datetime) -> str:
    row = bind.execute(sa.text("SELECT id FROM subscription_plans WHERE code = 'starter' LIMIT 1")).first()
    if row is not None:
        return str(row[0])
    plan_id = uuid4().hex
    bind.execute(
        sa.text(
            """
            INSERT INTO subscription_plans
            (id, code, name, description, price_amount, currency, requests_per_minute,
             content_generations_per_hour, publications_per_hour, features, is_active, created_at, updated_at)
            VALUES
            (:id, 'starter', 'Starter', 'Legacy starter plan', 0, 'RUB', 120, 100, 50, '{}', 1, :created_at, :updated_at)
            """
        ),
        {"id": plan_id, "created_at": now, "updated_at": now},
    )
    return plan_id


def _sqlite_has_column(bind, table_name: str, column_name: str) -> bool:
    rows = bind.execute(sa.text(f"PRAGMA table_info({table_name})")).mappings()
    return any(row["name"] == column_name for row in rows)
