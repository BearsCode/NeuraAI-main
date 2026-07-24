from __future__ import annotations

from sqlalchemy import ForeignKey, Index, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TenantTimePartitionMixin, UUIDPrimaryKeyMixin


class AuditLog(UUIDPrimaryKeyMixin, TenantTimePartitionMixin, Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_action_created", "tenant_id", "action", "created_at"),
        {"postgresql_partition_by": "RANGE (created_at)"},
    )

    user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(128), index=True)
    resource_type: Mapped[str] = mapped_column(String(64))
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
