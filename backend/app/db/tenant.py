from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from backend.app.db.enums import TenantStatus, enum_kwargs

if TYPE_CHECKING:
    from backend.app.db.project import Project
    from backend.app.db.subscription import Subscription
    from backend.app.db.tenant_membership import TenantMembership
    from backend.app.db.user import User


class Tenant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenants"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_tenants_slug"),
        Index("ix_tenants_status_created_at", "status", "created_at"),
    )

    slug: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[TenantStatus] = mapped_column(
        Enum(TenantStatus, **enum_kwargs),
        default=TenantStatus.ACTIVE,
        index=True,
    )
    owner_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
    )
    default_timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    industry: Mapped[str | None] = mapped_column(String(120), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    search_document: Mapped[str] = mapped_column(Text, default="")

    owner: Mapped["User"] = relationship()
    memberships: Mapped[list["TenantMembership"]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    projects: Mapped[list["Project"]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
