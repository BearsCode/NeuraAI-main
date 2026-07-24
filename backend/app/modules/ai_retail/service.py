from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.retail_catalog_sync import RetailCatalogSync
from backend.app.db.retail_product import RetailProduct
from backend.app.integrations.retail import RetailAdapterRegistry


class RetailService:
    async def connect_system(
        self,
        session: AsyncSession,
        tenant_id: str,
        project_id: str,
        source_system: str,
        credentials: dict,
    ) -> dict:
        sync = RetailCatalogSync(
            tenant_id=tenant_id,
            project_id=project_id,
            source_system=source_system,
            status="syncing",
            started_at=datetime.now(UTC),
        )
        session.add(sync)
        await session.flush()

        try:
            products = await self._fetch_products(source_system, credentials)
            synced = 0
            for prod_data in products:
                existing = await session.scalar(
                    select(RetailProduct).where(
                        RetailProduct.tenant_id == tenant_id,
                        RetailProduct.project_id == project_id,
                        RetailProduct.external_id == prod_data.get("external_id"),
                    )
                )
                if existing:
                    for key, value in prod_data.items():
                        setattr(existing, key, value)
                    existing.last_synced_at = datetime.now(UTC).isoformat()
                else:
                    product = RetailProduct(
                        tenant_id=tenant_id,
                        project_id=project_id,
                        source_system=source_system,
                        **{k: v for k, v in prod_data.items() if k in (
                            "external_id", "name", "description", "price", "old_price",
                            "currency", "category", "image_urls", "stock_quantity", "is_on_sale", "extra_data",
                        )},
                    )
                    session.add(product)
                synced += 1

            sync.status = "completed"
            sync.total_products = len(products)
            sync.synced_products = synced
            sync.completed_at = datetime.now(UTC)
            await session.commit()

            return {"status": "completed", "total": len(products), "synced": synced}
        except Exception as e:
            sync.status = "failed"
            sync.error = str(e)
            sync.completed_at = datetime.now(UTC)
            await session.commit()
            return {"status": "failed", "error": str(e)}

    async def sync_catalog(
        self, session: AsyncSession, tenant_id: str, project_id: str
    ) -> dict:
        return await self.connect_system(session, tenant_id, project_id, "scheduled", {})

    async def list_products(
        self,
        session: AsyncSession,
        tenant_id: str,
        project_id: str,
        category: str | None = None,
        on_sale: bool | None = None,
        in_stock: bool | None = None,
    ) -> list[dict]:
        query = select(RetailProduct).where(
            RetailProduct.tenant_id == tenant_id,
            RetailProduct.project_id == project_id,
            RetailProduct.is_active,
        )
        if category:
            query = query.where(RetailProduct.category == category)
        if on_sale is not None:
            query = query.where(RetailProduct.is_on_sale == on_sale)
        if in_stock is not None:
            if in_stock:
                query = query.where(RetailProduct.stock_quantity > 0)
            else:
                query = query.where(
                    (RetailProduct.stock_quantity == 0) | (RetailProduct.stock_quantity.is_(None))
                )

        products = (await session.scalars(query.order_by(desc(RetailProduct.updated_at)).limit(200))).all()
        return [self._product_to_dict(p) for p in products]

    async def get_dashboard(
        self, session: AsyncSession, tenant_id: str, project_id: str
    ) -> dict:
        total = await session.scalar(
            select(func.count(RetailProduct.id)).where(
                RetailProduct.tenant_id == tenant_id,
                RetailProduct.project_id == project_id,
                RetailProduct.is_active,
            )
        )
        on_sale = await session.scalar(
            select(func.count(RetailProduct.id)).where(
                RetailProduct.tenant_id == tenant_id,
                RetailProduct.project_id == project_id,
                RetailProduct.is_on_sale,
                RetailProduct.is_active,
            )
        )
        out_of_stock = await session.scalar(
            select(func.count(RetailProduct.id)).where(
                RetailProduct.tenant_id == tenant_id,
                RetailProduct.project_id == project_id,
                RetailProduct.is_active,
                RetailProduct.stock_quantity == 0,
            )
        )

        categories = (
            await session.scalars(
                select(RetailProduct.category)
                .where(
                    RetailProduct.tenant_id == tenant_id,
                    RetailProduct.project_id == project_id,
                    RetailProduct.is_active,
                    RetailProduct.category.isnot(None),
                )
                .distinct()
            )
        ).all()

        last_sync = await session.scalar(
            select(RetailCatalogSync)
            .where(
                RetailCatalogSync.tenant_id == tenant_id,
                RetailCatalogSync.project_id == project_id,
            )
            .order_by(desc(RetailCatalogSync.created_at))
            .limit(1)
        )

        return {
            "total_products": total or 0,
            "on_sale_count": on_sale or 0,
            "out_of_stock_count": out_of_stock or 0,
            "categories": list(categories),
            "last_sync": {
                "status": last_sync.status if last_sync else None,
                "total": last_sync.total_products if last_sync else None,
                "synced": last_sync.synced_products if last_sync else None,
                "error": last_sync.error if last_sync else None,
                "created_at": last_sync.created_at.isoformat() if last_sync else None,
            } if last_sync else None,
        }

    async def get_sync_history(
        self, session: AsyncSession, tenant_id: str, project_id: str
    ) -> list[dict]:
        syncs = (
            await session.scalars(
                select(RetailCatalogSync)
                .where(
                    RetailCatalogSync.tenant_id == tenant_id,
                    RetailCatalogSync.project_id == project_id,
                )
                .order_by(desc(RetailCatalogSync.created_at))
                .limit(30)
            )
        ).all()

        return [
            {
                "id": s.id,
                "source_system": s.source_system,
                "status": s.status,
                "total_products": s.total_products,
                "synced_products": s.synced_products,
                "error": s.error,
                "created_at": s.created_at.isoformat(),
            }
            for s in syncs
        ]

    async def _fetch_products(self, source_system: str, credentials: dict) -> list[dict]:
        adapter_cls = RetailAdapterRegistry.get(source_system)
        if not adapter_cls:
            raise ValueError(f"Unknown retail system: {source_system}")
        adapter = adapter_cls()
        return await adapter.fetch_products(credentials)

    def _product_to_dict(self, p: RetailProduct) -> dict:
        return {
            "id": p.id,
            "external_id": p.external_id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "old_price": p.old_price,
            "currency": p.currency,
            "category": p.category,
            "image_urls": p.image_urls,
            "stock_quantity": p.stock_quantity,
            "is_on_sale": p.is_on_sale,
            "source_system": p.source_system,
            "last_synced_at": p.last_synced_at,
            "created_at": p.created_at.isoformat(),
        }
