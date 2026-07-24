from __future__ import annotations

from sqlalchemy import Boolean, Float, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RetailProduct(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "retail_products"

    tenant_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    project_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    external_id: Mapped[str] = mapped_column(String(256), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    old_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    category: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    image_urls: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    stock_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_on_sale: Mapped[bool] = mapped_column(Boolean, default=False)
    sale_ends_at: Mapped[str | None] = mapped_column(nullable=True)
    source_system: Mapped[str | None] = mapped_column(String(64), nullable=True)
    extra_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    last_synced_at: Mapped[str | None] = mapped_column(nullable=True)
