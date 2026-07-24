from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RetailCatalogSync(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "retail_catalog_syncs"

    tenant_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    project_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    total_products: Mapped[int | None] = mapped_column(Integer, nullable=True)
    synced_products: Mapped[int | None] = mapped_column(Integer, nullable=True)
    failed_products: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
