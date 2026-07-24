from __future__ import annotations

from typing import Any

import httpx

from backend.app.integrations.retail.base import RetailAdapter, RetailAdapterRegistry


class AmoCRMAdapter(RetailAdapter):
    async def check_connection(self, credentials: dict) -> bool:
        base_url = self._base_url(credentials)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{base_url}/api/v4/account",
                    headers=self._headers(credentials),
                )
                return response.status_code == 200
        except Exception:
            return False

    async def fetch_products(self, credentials: dict) -> list[dict[str, Any]]:
        base_url = self._base_url(credentials)
        headers = self._headers(credentials)
        products: list[dict[str, Any]] = []
        url: str | None = f"{base_url}/api/v4/catalog_elements?limit=250"

        async with httpx.AsyncClient(timeout=60.0) as client:
            while url:
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    raise RuntimeError(
                        f"AmoCRM API returned {response.status_code}: {response.text[:200]}"
                    )
                data = response.json()
                rows = data.get("_embedded", {}).get("catalog_elements", [])
                for row in rows:
                    if product := self._parse_product(row):
                        products.append(product)
                links = data.get("_links", {})
                url = links.get("next", {}).get("href") if isinstance(links.get("next"), dict) else None

        return products

    def _parse_product(self, row: dict[str, Any]) -> dict[str, Any] | None:
        external_id = str(row.get("id", ""))
        name = str(row.get("name", "")).strip()
        if not name:
            return None

        cf = {f["id"]: f.get("values", [{}])[0].get("value") for f in row.get("custom_fields_values", []) if f.get("id")}
        price_str = str(cf.get("PRICE", "0")).replace(",", ".").replace(" ", "")
        try:
            price = float(price_str)
        except (ValueError, TypeError):
            price = 0.0

        return self._normalize_product({
            "external_id": external_id,
            "name": name,
            "description": row.get("description", "") or "",
            "price": price,
            "old_price": None,
            "currency": "RUB",
            "category": str(cf.get("CATEGORY", "")),
            "image_urls": [],
            "stock_quantity": None,
            "is_on_sale": False,
        })

    def _base_url(self, credentials: dict) -> str:
        subdomain = credentials.get("subdomain", "example")
        return f"https://{subdomain}.amocrm.ru"

    def _headers(self, credentials: dict) -> dict[str, str]:
        token = credentials.get("access_token", "")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @staticmethod
    def _normalize_product(raw: dict[str, Any]) -> dict[str, Any]:
        return raw


RetailAdapterRegistry.register("amocrm", AmoCRMAdapter)
