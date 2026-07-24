from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin
from backend.app.db.enums import IntegrationPlatform, IntegrationStatus, enum_kwargs

if TYPE_CHECKING:
    from backend.app.db.project import Project
    from backend.app.db.publication_target import PublicationTarget


class SocialIntegration(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, Base):
    __tablename__ = "social_integrations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "project_id", "platform", name="uq_social_integrations_project_platform"),
        Index("ix_social_integrations_tenant_status", "tenant_id", "status"),
    )

    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    platform: Mapped[IntegrationPlatform] = mapped_column(Enum(IntegrationPlatform, **enum_kwargs), index=True)
    account_handle: Mapped[str] = mapped_column(String(255))
    status: Mapped[IntegrationStatus] = mapped_column(
        Enum(IntegrationStatus, **enum_kwargs),
        default=IntegrationStatus.PENDING,
        index=True,
    )
    encrypted_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    encrypted_refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    autoposting_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    publication_settings: Mapped[dict] = mapped_column(JSON, default=dict)
    scopes: Mapped[list[str]] = mapped_column(JSON, default=list)

    project: Mapped["Project"] = relationship(back_populates="integrations")
    publication_targets: Mapped[list["PublicationTarget"]] = relationship(back_populates="integration")
