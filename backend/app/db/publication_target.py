from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin
from backend.app.db.enums import IntegrationPlatform, PublicationTargetStatus, enum_kwargs

if TYPE_CHECKING:
    from backend.app.db.publication import Publication
    from backend.app.db.publication_attempt import PublicationAttempt
    from backend.app.db.social_integration import SocialIntegration


class PublicationTarget(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, Base):
    __tablename__ = "publication_targets"
    __table_args__ = (
        UniqueConstraint("publication_id", "integration_id", name="uq_publication_targets"),
        Index("ix_publication_targets_tenant_status", "tenant_id", "status"),
    )

    publication_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("publications.id", ondelete="CASCADE"),
        index=True,
    )
    integration_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("social_integrations.id", ondelete="RESTRICT"),
        index=True,
    )
    platform: Mapped[IntegrationPlatform] = mapped_column(Enum(IntegrationPlatform, **enum_kwargs), index=True)
    status: Mapped[PublicationTargetStatus] = mapped_column(
        Enum(PublicationTargetStatus, **enum_kwargs),
        default=PublicationTargetStatus.QUEUED,
        index=True,
    )
    external_post_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    compensate_required: Mapped[bool] = mapped_column(Boolean, default=False)

    publication: Mapped["Publication"] = relationship(back_populates="targets")
    integration: Mapped["SocialIntegration"] = relationship(back_populates="publication_targets")
    attempts: Mapped[list["PublicationAttempt"]] = relationship(
        back_populates="target",
        cascade="all, delete-orphan",
    )
