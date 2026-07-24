from __future__ import annotations

from typing import Any

import httpx

from backend.app.integrations.retail.base import RetailAdapter, RetailAdapterRegistry


class Bitrix24Adapter(RetailAdapter):
    async def check_connection(self, credentials: dict) -> bool:
        webhook_url = self._webhook_url(credentials)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{webhook_url}crm.product.list",
                    json={"limit": 1},
                )
                return response.status_code == 200
        except Exception:
            return False

    async def fetch_products(self, credentials: dict) -> list[dict[str, Any]]:
        webhook_url = self._webhook_url(credentials)
        products: list[dict[str, Any]] = []
        start = 0

        async with httpx.AsyncClient(timeout=60.0) as client:
            while True:
                response = await client.post(
                    f"{webhook_url}crm.product.list",
                    json={"limit": 50, "start": start},
                )
                if response.status_code != 200:
                    raise RuntimeError(
                        f"Bitrix24 API returned {response.status_code}: {response.text[:200]}"
                    )
                data = response.json()
                if data.get("error"):
                    raise RuntimeError(
                        f"Bitrix24 error: {data.get('error_description', data['error'])}"
                    )
                rows = data.get("result", [])
                for row in rows:
                    if product := self._parse_product(row):
                        products.append(product)

                total = data.get("total", len(rows) + start)
                start += len(rows)
                if start >= total or not rows:
                    break

        return products

    def _parse_product(self, row: dict[str, Any]) -> dict[str, Any] | None:
        external_id = str(row.get("ID", ""))
        name = str(row.get("NAME", "")).strip()
        if not name:
            return None

        price_str = str(row.get("PRICE", "0")).replace(",", ".").replace(" ", "")
        try:
            price = float(price_str)
        except (ValueError, TypeError):
            price = 0.0

        currency = str(row.get("CURRENCY_ID", "RUB") or "RUB")

        return self._normalize_product({
            "external_id": external_id,
            "name": name,
            "description": str(row.get("DESCRIPTION", "") or ""),
            "price": price,
            "old_price": None,
            "currency": currency,
            "category": str(row.get("SECTION", {}).get("NAME", "") if isinstance(row.get("SECTION"), dict) else ""),
            "image_urls": [],
            "stock_quantity": None,
            "is_on_sale": False,
        })

    def _webhook_url(self, credentials: dict) -> str:
        base = credentials.get("base_url", "").rstrip("/")
        if not base.endswith("/rest/"):
            base = f"{base}/rest/"
        return base

    @staticmethod
    def _normalize_product(raw: dict[str, Any]) -> dict[str, Any]:
        return raw


RetailAdapterRegistry.register("bitrix24", Bitrix24Adapter)
