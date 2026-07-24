
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from backend.app.db.enums import AdminRole, UserRole, enum_kwargs

if TYPE_CHECKING:
    from backend.app.db.partner_commission import PartnerCommission
    from backend.app.db.partner_profile import PartnerProfile
    from backend.app.db.refresh_token_session import RefreshTokenSession
    from backend.app.db.tenant_membership import TenantMembership


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_role_is_active", "role", "is_active"),
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    vk_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    yandex_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    mailru_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    telegram_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, **enum_kwargs), index=True)
    admin_role: Mapped[AdminRole | None] = mapped_column(
        Enum(AdminRole, **enum_kwargs), nullable=True, index=True
    )
    encrypted_permissions: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    referred_by_user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    referred_by: Mapped["User | None"] = relationship(remote_side="User.id", backref="referrals")
    partner_profile: Mapped["PartnerProfile | None"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    memberships: Mapped[list["TenantMembership"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    refresh_sessions: Mapped[list["RefreshTokenSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    commissions: Mapped[list["PartnerCommission"]] = relationship(back_populates="partner_user")
