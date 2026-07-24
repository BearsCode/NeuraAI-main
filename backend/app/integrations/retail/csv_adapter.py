from __future__ import annotations

import csv
import io
from typing import Any

import httpx

from backend.app.integrations.retail.base import RetailAdapter, RetailAdapterRegistry
from backend.app.integrations.retail.google_sheets import GoogleSheetsAdapter


class CSVRetailAdapter(RetailAdapter):
    COLUMN_MAP = GoogleSheetsAdapter.COLUMN_MAP

    async def check_connection(self, credentials: dict) -> bool:
        url = credentials.get("url", "")
        if url:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.head(url)
                    return response.status_code < 500
            except Exception:
                return False
        file_path = credentials.get("file_path", "")
        if file_path:
            try:
                import os as _os
                return _os.path.isfile(file_path)
            except Exception:
                return False
        content = credentials.get("content", "")
        return bool(content.strip())

    async def fetch_products(self, credentials: dict) -> list[dict[str, Any]]:
        raw_content = await self._load_content(credentials)
        reader = csv.DictReader(io.StringIO(raw_content))
        if reader.fieldnames is None:
            return []

        header = [h.strip().lower() for h in reader.fieldnames]
        col_idx: dict[str, int] = {}
        for expected, aliases in self.COLUMN_MAP.items():
            for alias in aliases:
                if alias in header:
                    col_idx[expected] = header.index(alias)
                    break

        products: list[dict[str, Any]] = []
        for row in reader:
            row_list = [str(row.get(h, "")) for h in reader.fieldnames]
            product = self._parse_row(row_list, col_idx)
            if product:
                products.append(product)

        return products

    async def _load_content(self, credentials: dict) -> str:
        url = credentials.get("url", "")
        if url:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text

        file_path = credentials.get("file_path", "")
        if file_path:
            import aiofiles
            async with aiofiles.open(file_path, "r", encoding="utf-8-sig") as f:
                return await f.read()

        return credentials.get("content", "")

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

    @staticmethod
    def _normalize_product(raw: dict[str, Any]) -> dict[str, Any]:
        return raw


RetailAdapterRegistry.register("csv", CSVRetailAdapter)
