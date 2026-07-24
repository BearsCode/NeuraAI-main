from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin
from backend.app.db.enums import AssetType, enum_kwargs

if TYPE_CHECKING:
    from backend.app.db.project import Project


class Asset(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, Base):
    __tablename__ = "assets"
    __table_args__ = (
        Index("ix_assets_tenant_project_type", "tenant_id", "project_id", "asset_type"),
    )

    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType, **enum_kwargs), index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(120))
    storage_uri: Mapped[str] = mapped_column(String(500))
    public_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)

    project: Mapped["Project"] = relationship(back_populates="assets")
