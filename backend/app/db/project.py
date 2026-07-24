from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin
from backend.app.db.enums import StrategyStatus, enum_kwargs

if TYPE_CHECKING:
    from backend.app.db.analytics_snapshot import AnalyticsSnapshot
    from backend.app.db.approval_policy import ApprovalPolicy
    from backend.app.db.asset import Asset
    from backend.app.db.content_item import ContentItem
    from backend.app.db.content_plan import ContentPlan
    from backend.app.db.project_strategy import ProjectStrategy
    from backend.app.db.publication import Publication
    from backend.app.db.social_integration import SocialIntegration
    from backend.app.db.tenant import Tenant
    from backend.app.db.user import User


class Project(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (
        Index("ix_projects_tenant_status_created", "tenant_id", "strategy_status", "created_at"),
    )

    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        index=True,
    )
    owner_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
    )
    company_name: Mapped[str] = mapped_column(String(255))
    company_inn: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    business_description: Mapped[str] = mapped_column(Text)
    city: Mapped[str] = mapped_column(String(120))
    industry: Mapped[str] = mapped_column(String(120))
    services: Mapped[list[str]] = mapped_column(JSON, default=list)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    social_links: Mapped[list[str]] = mapped_column(JSON, default=list)
    target_audience: Mapped[str] = mapped_column(Text)
    competitors: Mapped[list[str]] = mapped_column(JSON, default=list)
    business_features: Mapped[list[str]] = mapped_column(JSON, default=list)
    strategy_status: Mapped[StrategyStatus] = mapped_column(
        Enum(StrategyStatus, **enum_kwargs),
        default=StrategyStatus.DRAFT,
        index=True,
    )
    offer_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    data_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    onboarding_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    search_document: Mapped[str] = mapped_column(Text, default="")

    tenant: Mapped["Tenant"] = relationship(back_populates="projects")
    owner: Mapped["User"] = relationship()
    assets: Mapped[list["Asset"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    integrations: Mapped[list["SocialIntegration"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    strategy: Mapped["ProjectStrategy | None"] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        uselist=False,
    )
    content_plans: Mapped[list["ContentPlan"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    content_items: Mapped[list["ContentItem"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    publications: Mapped[list["Publication"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    approval_policy: Mapped["ApprovalPolicy | None"] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        uselist=False,
    )
    analytics_snapshots: Mapped[list["AnalyticsSnapshot"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
