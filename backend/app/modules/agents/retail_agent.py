from __future__ import annotations

from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.retail_product import RetailProduct
from backend.app.integrations import ai_client
from backend.app.modules.agents.base import BaseAgent


class RetailAgent(BaseAgent):
    name = "retail"
    description = "Выбор товара и генерация товарного поста"

    async def execute(
        self,
        session: AsyncSession,
        input_data: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        project_id = input_data.get("project_id", (context or {}).get("project_id"))
        tenant_id = input_data.get("tenant_id", (context or {}).get("tenant_id"))

        priority = input_data.get("priority", "newest")
        category_filter = input_data.get("category")

        query = select(RetailProduct).where(
            RetailProduct.tenant_id == tenant_id,
            RetailProduct.project_id == project_id,
            RetailProduct.is_active,
        )
        if category_filter:
            query = query.where(RetailProduct.category == category_filter)

        if priority == "on_sale":
            query = query.where(RetailProduct.is_on_sale).order_by(desc(RetailProduct.updated_at))
        elif priority == "in_stock":
            query = query.where(RetailProduct.stock_quantity > 0).order_by(desc(RetailProduct.updated_at))
        else:
            query = query.order_by(desc(RetailProduct.created_at))

        products = (await session.scalars(query.limit(5))).all()

        if not products:
            return {"selected_product": None, "message": "No products available"}

        product = products[0]

        return {
            "selected_product": {
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "old_price": product.old_price,
                "currency": product.currency,
                "category": product.category,
                "image_urls": product.image_urls,
                "is_on_sale": product.is_on_sale,
                "description": product.description,
                "stock_quantity": product.stock_quantity,
                "source_system": product.source_system,
            },
            "available_count": len(products),
            "priority_used": priority,
        }

    async def process_catalog_file(self, file_path: str, format_type: str) -> dict[str, Any]:
        """
        Парсер файлов Excel/CSV/YML.
        Реализовано с использованием pandas и pyyaml для импорта товаров.
        """
        import os
        import pandas as pd
        import yaml
        
        if not os.path.exists(file_path):
            return {"status": "error", "error": f"File not found: {file_path}"}
            
        try:
            df = None
            if format_type.lower() == "csv":
                df = pd.read_csv(file_path)
            elif format_type.lower() in ["excel", "xlsx", "xls"]:
                df = pd.read_excel(file_path)
            elif format_type.lower() in ["yaml", "yml"]:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if isinstance(data, dict) and "items" in data:
                    df = pd.DataFrame(data["items"])
                elif isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    return {"status": "error", "error": "Invalid YAML structure for catalog"}
            else:
                return {"status": "error", "error": f"Unsupported format: {format_type}"}
                
            if df is None or df.empty:
                return {"status": "success", "imported_count": 0, "errors": [], "source": "file_import", "format": format_type}
                
            # Basic column mapping: convert to lower case for easier matching
            df.columns = [str(c).lower().strip() for c in df.columns]
            
            # Identify columns
            name_col = next((c for c in df.columns if c in ["name", "title", "название", "товар"]), None)
            price_col = next((c for c in df.columns if c in ["price", "цена", "стоимость"]), None)
            desc_col = next((c for c in df.columns if c in ["description", "описание", "desc"]), None)
            cat_col = next((c for c in df.columns if c in ["category", "категория", "type", "категории"]), None)
            
            if not name_col or not price_col:
                return {"status": "error", "error": "Missing required columns: name or price"}
                
            imported_items = []
            errors = []
            
            for index, row in df.iterrows():
                try:
                    item_name = str(row[name_col]).strip()
                    if not item_name or item_name == "nan":
                        errors.append({"row": index + 1, "error": "Empty name"})
                        continue
                        
                    price_val = row[price_col]
                    # Attempt to clean price
                    if isinstance(price_val, str):
                        price_val = ''.join(c for c in price_val if c.isdigit() or c in '.,')
                        price_val = price_val.replace(',', '.')
                    
                    price = float(price_val)
                    
                    item = {
                        "name": item_name,
                        "price": price,
                        "description": str(row[desc_col]).strip() if desc_col and str(row[desc_col]) != "nan" else "",
                        "category": str(row[cat_col]).strip() if cat_col and str(row[cat_col]) != "nan" else "",
                    }
                    imported_items.append(item)
                except Exception as row_e:
                    errors.append({"row": index + 1, "error": str(row_e)})
                    
            return {
                "status": "success",
                "imported_count": len(imported_items),
                "error_count": len(errors),
                "errors": errors[:10], # Return max 10 errors to avoid huge payloads
                "items": imported_items, # Returning parsed items
                "source": "file_import",
                "format": format_type
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def process_menu_photo(self, photo_url: str) -> dict[str, Any]:
        """
        P2 feature: Vision-модель для распознавания всего меню с одной фотографии.
        Раскладывает текст (блюда, категории, цены) на отдельные карточки.
        """
        prompt = (
            "Analyze the following menu photo. Extract all items, categories, and prices.\n"
            f"Image URL: {photo_url}\n"
            "Return JSON with a list of 'items' (name, category, price, description)."
        )
        
        try:
            result = await ai_client.generate(prompt=prompt, response_format={"type": "json_object"})
            parsed_items = result.get("items", [])
            # In a real app, we would insert these into RetailProduct table
            
            return {
                "status": "success",
                "parsed_count": len(parsed_items),
                "items": parsed_items,
                "source": "manual_photo"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
