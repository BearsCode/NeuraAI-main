from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.integrations import ai_client
from backend.app.modules.agents.base import BaseAgent


class BrandAgent(BaseAgent):
    name = "brand"
    description = "Анализ визуального стиля и материалов соцсетей"

    async def execute(
        self,
        session: AsyncSession,
        input_data: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        uploaded_materials = input_data.get("materials", [])
        social_links = input_data.get("social_links", [])

        # uploaded_materials is expected to be a list of URLs
        image_urls = [m for m in uploaded_materials if isinstance(m, str) and m.startswith("http")]

        prompt = (
            f"Analyze brand visual style from these materials and social links.\n"
            f"Uploaded materials count: {len(uploaded_materials)}\n"
            f"Social links: {social_links}\n"
            f"Return JSON with: brand_colors (list), brand_fonts (list), "
            f"visual_style (str), image_tone (str), recommendations (list)"
        )

        result = await ai_client.generate(
            prompt=prompt, 
            response_format={"type": "json_object"},
            images=image_urls if image_urls else None
        )
        return result if isinstance(result, dict) else {"brand_analysis": str(result)}
