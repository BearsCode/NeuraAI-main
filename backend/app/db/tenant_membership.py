from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from backend.app.db.enums import MembershipRole, enum_kwargs

if TYPE_CHECKING:
    from backend.app.db.tenant import Tenant
    from backend.app.db.user import User


class TenantMembership(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenant_memberships"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_tenant_membership_user"),
        Index("ix_tenant_memberships_role", "tenant_id", "role"),
    )

    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    role: Mapped[MembershipRole] = mapped_column(Enum(MembershipRole, **enum_kwargs))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    tenant: Mapped["Tenant"] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship(back_populates="memberships")
