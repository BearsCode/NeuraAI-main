from __future__ import annotations

from typing import Any

import httpx

from backend.app.integrations.retail.base import RetailAdapter, RetailAdapterRegistry


class GoogleSheetsAdapter(RetailAdapter):
    COLUMN_MAP = {
        "external_id": ["id", "sku", "article", "артикул", "external_id", "product_id"],
        "name": ["name", "название", "product_name", "title", "товар"],
        "description": ["description", "описание", "desc"],
        "price": ["price", "цена", "cost", "стоимость", "price_rub"],
        "old_price": ["old_price", "old price", "старая цена"],
        "currency": ["currency", "валюта"],
        "category": ["category", "категория", "cat", "group", "группа"],
        "image_urls": ["image", "images", "img", "image_url", "фото", "картинка"],
        "stock_quantity": ["stock", "quantity", "остаток", "количество", "stock_quantity", "qty"],
    }

    async def check_connection(self, credentials: dict) -> bool:
        sheet_id = self._sheet_id(credentials)
        api_key = credentials.get("api_key", "")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/A1:Z1",
                    params={"key": api_key} if api_key else {},
                )
                return response.status_code == 200
        except Exception:
            return False

    async def fetch_products(self, credentials: dict) -> list[dict[str, Any]]:
        sheet_id = self._sheet_id(credentials)
        range_str = credentials.get("range", "A:Z")
        api_key = credentials.get("api_key", "")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{range_str}",
                params={"key": api_key} if api_key else {},
            )
            if response.status_code != 200:
                raise RuntimeError(
                    f"Google Sheets API returned {response.status_code}: {response.text[:200]}"
                )
            data = response.json()
            values = data.get("values", [])
            if not values:
                return []

            header = [str(h).strip().lower() for h in values[0]]
            col_idx: dict[str, int] = {}
            for expected, aliases in self.COLUMN_MAP.items():
                for alias in aliases:
                    if alias in header:
                        col_idx[expected] = header.index(alias)
                        break

            products: list[dict[str, Any]] = []
            for row in values[1:]:
                product = self._parse_row(row, col_idx)
                if product:
                    products.append(product)

        return products

    def _parse_row(self, row: list[str], col_idx: dict[str, int]) -> dict[str, Any] | None:
        def _get(col: str) -> str:
            i = col_idx.get(col)
            return str(row[i]).strip() if i is not None and i < len(row) else ""

        name = _get("name")
        if not name:
            return None

        price_str = _get("price").replace(",", ".").replace(" ", "")
        try:
            price = float(price_str)
        except (ValueError, TypeError):
            price = 0.0

        old_price_str = _get("old_price").replace(",", ".").replace(" ", "")
        try:
            old_price = float(old_price_str)
        except (ValueError, TypeError):
            old_price = None

        stock_str = _get("stock_quantity").replace(",", ".").replace(" ", "")
        try:
            stock = int(float(stock_str))
        except (ValueError, TypeError):
            stock = None

        images_raw = _get("image_urls")
        image_urls = [u.strip() for u in images_raw.split(",") if u.strip()] if images_raw else []

        return self._normalize_product({
            "external_id": _get("external_id"),
            "name": name,
            "description": _get("description"),
            "price": price,
            "old_price": old_price,
            "currency": _get("currency") or "RUB",
            "category": _get("category"),
            "image_urls": image_urls,
            "stock_quantity": stock,
            "is_on_sale": old_price is not None and old_price > price,
        })

    def _sheet_id(self, credentials: dict) -> str:
        return credentials.get("spreadsheet_id", credentials.get("sheet_id", ""))

    @staticmethod
    def _normalize_product(raw: dict[str, Any]) -> dict[str, Any]:
        return raw


RetailAdapterRegistry.register("google_sheets", GoogleSheetsAdapter)
