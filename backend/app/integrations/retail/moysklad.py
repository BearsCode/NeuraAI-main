from __future__ import annotations

from typing import Any

import httpx

from backend.app.core.configs import settings
from backend.app.integrations.retail.base import RetailAdapter, RetailAdapterRegistry

MOYSKLAD_API = "https://api.moysklad.ru/api/remap/1.2"


class MoyskladRestAdapter(RetailAdapter):
    async def check_connection(self, credentials: dict) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{MOYSKLAD_API}/entity/product?limit=1",
                    headers=self._headers(credentials),
                )
                return response.status_code == 200
        except Exception:
            return False

    async def fetch_products(self, credentials: dict) -> list[dict[str, Any]]:
        headers = self._headers(credentials)
        products: list[dict[str, Any]] = []
        url: str | None = f"{MOYSKLAD_API}/entity/product?limit=100&expand=images"

        async with httpx.AsyncClient(timeout=60.0) as client:
            while url:
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    raise RuntimeError(
                        f"МойСклад API returned {response.status_code}: {response.text[:200]}"
                    )

                data = response.json()
                rows = data.get("rows", [])
                for row in rows:
                    if product := self._parse_product(row):
                        products.append(product)

                url = data.get("meta", {}).get("nextHref")

        return products

    def _parse_product(self, row: dict[str, Any]) -> dict[str, Any] | None:
        name = row.get("name", "").strip()
        external_id = row.get("id") or row.get("externalCode", "")
        if not name or not external_id:
            return None

        price_info = row.get("salePrices", [{}])[0] if row.get("salePrices") else {}
        price_value = price_info.get("value", 0)
        price = price_value / 100 if price_value else 0.0

        currency_meta = price_info.get("currency", {})
        currency = currency_meta.get("name", "RUB") if currency_meta else "RUB"

        stock = row.get("quantity", None)
        if stock is not None:
            try:
                stock = int(stock)
            except (ValueError, TypeError):
                stock = None

        category = ""
        group_meta = row.get("productFolder", {}).get("meta", {})
        if group_meta.get("href"):
            category = group_meta.get("href", "").rsplit("/", 1)[-1]

        image_urls = []
        images_meta = row.get("images", {}).get("meta", {})
        if images_meta.get("href"):
            image_urls = [images_meta["href"]]

        description = row.get("description", "") or ""

        return self._normalize_product(
            {
                "external_id": external_id,
                "name": name,
                "description": description,
                "price": price,
                "old_price": None,
                "currency": currency,
                "category": category,
                "image_urls": image_urls,
                "stock_quantity": stock,
                "is_on_sale": False,
            }
        )

    def _headers(self, credentials: dict) -> dict[str, str]:
        token = credentials.get("token") or settings.retail.moysklad_token.get_secret_value()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @staticmethod
    def _normalize_product(raw: dict[str, Any]) -> dict[str, Any]:
        return raw


RetailAdapterRegistry.register("moysklad", MoyskladRestAdapter)
