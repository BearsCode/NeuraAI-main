from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

import httpx

from backend.app.core.configs import settings
from backend.app.integrations.retail.base import RetailAdapter, RetailAdapterRegistry

class C1CommerceMLAdapter(RetailAdapter):
    async def check_connection(self, credentials: dict) -> bool:
        url = self._base_url(credentials).rstrip("/") + "/status"
        try:
            auth = self._auth(credentials)
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, auth=auth)
                return response.status_code < 500
        except Exception:
            return False

    async def fetch_products(self, credentials: dict) -> list[dict[str, Any]]:
        base_url = self._base_url(credentials).rstrip("/")
        auth = self._auth(credentials)
        import_url = f"{base_url}/import.xml"

        products: list[dict[str, Any]] = []

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(import_url, auth=auth)
            if response.status_code != 200:
                raise RuntimeError(
                    f"1C import.xml returned {response.status_code}: {response.text[:200]}"
                )

            root = ET.fromstring(response.content)

            def _ns(name: str) -> str:
                return f"{{http://www.v8.1c.ru/edi/CommerceML2.0}}{name}"

            ns_products = root.findall(f".//{_ns('Товар')}")
            if ns_products:
                for catalog in root.findall(f".//{_ns('Каталог')}"):
                    for group_elem in catalog.findall(f"{_ns('Группы')}/{_ns('Группа')}"):
                        category_name = group_elem.findtext(f"{_ns('Наименование')}", "")

                        for product_elem in catalog.findall(f"{_ns('Товары')}/{_ns('Товар')}"):
                            product = self._parse_product(product_elem, category_name)
                            if product:
                                products.append(product)

                if not products:
                    for product_elem in ns_products:
                        product = self._parse_product(product_elem, "")
                        if product:
                            products.append(product)
            else:
                for product_elem in root.findall(".//Товар"):
                    product = self._parse_product(product_elem, "")
                    if product:
                        products.append(product)

                if not products:
                    for elem in root.iter():
                        if "Товар" in elem.tag:
                            product = self._parse_product(elem, "")
                            if product:
                                products.append(product)

        return products

    def _parse_product(
        self, elem: ET.Element, default_category: str
    ) -> dict[str, Any] | None:
        tag = elem.tag
        ns = tag[tag.index("}") + 1:] if "}" in tag else tag
        if "Товар" not in ns:
            return None

        external_id = elem.get("Ид") or ""
        name_el = elem.find("Наименование") or elem.find("{http://www.v8.1c.ru/edi/CommerceML2.0}Наименование")
        name = name_el.text.strip() if name_el is not None and name_el.text else ""
        if not external_id or not name:
            return None

        desc_el = elem.find("Описание") or elem.find("{http://www.v8.1c.ru/edi/CommerceML2.0}Описание")
        description = desc_el.text.strip() if desc_el is not None and desc_el.text else ""

        group_el = elem.find("Группы") or elem.find("{http://www.v8.1c.ru/edi/CommerceML2.0}Группы")
        category = default_category
        if group_el is not None:
            id_el = group_el.find("Ид") or group_el.find("{http://www.v8.1c.ru/edi/CommerceML2.0}Ид")
            if id_el is not None and id_el.text:
                category = id_el.text

        price = 0.0
        currency = "RUB"
        prices_el = elem.find("Цены") or elem.find("{http://www.v8.1c.ru/edi/CommerceML2.0}Цены")
        if prices_el is not None:
            price_el = prices_el.find("Цена") or prices_el.find("{http://www.v8.1c.ru/edi/CommerceML2.0}Цена")
            if price_el is not None:
                ppu_el = price_el.find("ЦенаЗаЕдиницу") or price_el.find("{http://www.v8.1c.ru/edi/CommerceML2.0}ЦенаЗаЕдиницу")
                if ppu_el is not None and ppu_el.text:
                    price = float(ppu_el.text)
                curr_el = price_el.find("Валюта") or price_el.find("{http://www.v8.1c.ru/edi/CommerceML2.0}Валюта")
                if curr_el is not None and curr_el.text:
                    currency = curr_el.text

        stock = None
        qty_el = elem.find("Количество") or elem.find("{http://www.v8.1c.ru/edi/CommerceML2.0}Количество")
        if qty_el is not None and qty_el.text:
            try:
                stock = int(float(qty_el.text))
            except (ValueError, TypeError):
                pass

        image_urls = []
        img_el = elem.find("Картинка") or elem.find("{http://www.v8.1c.ru/edi/CommerceML2.0}Картинка")
        if img_el is not None and img_el.text:
            image_urls = [img_el.text]

        return self._normalize_product({
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
        })

    def _base_url(self, credentials: dict) -> str:
        return credentials.get("base_url") or settings.retail.c1_base_url

    def _auth(self, credentials: dict) -> httpx.BasicAuth | None:
        login = credentials.get("login") or settings.retail.c1_login
        password = credentials.get("password") or settings.retail.c1_password.get_secret_value()
        if login and password:
            return httpx.BasicAuth(login, password)
        return None

    @staticmethod
    def _normalize_product(raw: dict[str, Any]) -> dict[str, Any]:
        return raw


RetailAdapterRegistry.register("1c", C1CommerceMLAdapter)
