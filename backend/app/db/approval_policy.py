from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin
from backend.app.db.enums import ApprovalMode, enum_kwargs

if TYPE_CHECKING:
    from backend.app.db.project import Project


class ApprovalPolicy(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, Base):
    __tablename__ = "approval_policies"
    __table_args__ = (
        UniqueConstraint("project_id", name="uq_approval_policies_project_id"),
    )

    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        unique=True,
    )
    mode: Mapped[ApprovalMode] = mapped_column(
        Enum(ApprovalMode, **enum_kwargs),
        default=ApprovalMode.MANUAL,
    )
    auto_publish_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_publish_platforms: Mapped[list[str]] = mapped_column(JSON, default=list)

    project: Mapped["Project"] = relationship(back_populates="approval_policy")
