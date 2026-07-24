from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.integrations import ai_client, storage_client
from backend.app.modules.agents.base import BaseAgent
from backend.app.services_internal.business_memory import BusinessMemoryService


class TimelapseAgent(BaseAgent):
    name = "timelapse"
    description = "Таймлапс Агент: Визуализация процесса (ремонт, стройка и т.д.)"

    def __init__(self):
        self.memory = BusinessMemoryService()

    async def analyze_project(self, project_data: str) -> str:
        prompt = f"Анализ материалов проекта: {project_data}. Определи тип процесса (строительство, ремонт помещения, производство изделия, подготовка к открытию точки). Верни JSON с полем process_type."
        res = await ai_client.generate(prompt=prompt, response_format={"type": "json_object"})
        if isinstance(res, dict):
            return res.get("process_type", "unknown process")
        return "unknown process"

    async def build_stages(self, process_type: str, project_data: str) -> list[dict[str, Any]]:
        prompt = f"Построй этапы для процесса '{process_type}' на основе {project_data}. От 5 до 9 этапов. Верни JSON с полем stages (массив объектов с stage_number, title, description, environment_details)."
        res = await ai_client.generate(prompt=prompt, response_format={"type": "json_object"})
        if isinstance(res, dict):
            return res.get("stages", [])
        return []

    async def plan_camera(self, process_type: str, stages: list[dict[str, Any]]) -> dict[str, Any]:
        prompt = f"""ROLE
Ты — Таймлапс Агент платформы Нейра. Ты создаёшь кинематографичные визуализации протяжённого во времени процесса.

MISSION
На основе предоставленных материалов проекта построить логичную последовательность этапов и сгенерировать сценарий таймлапс-видео с движением камеры.

RULES
1. Всегда запрашивай тип процесса явно, если он не указан.
2. Количество этапов — от 5 до 9.
3. Каждый этап должен логически следовать из предыдущего.
4. Окружение и детали добавляй только уместные.
5. Движение камеры (orbit, zoom, pan, flythrough, static) должно быть разнообразным — не более 2 одинаковых подряд.
6. Финальная сцена обязательно содержит логотип и контакты бизнеса.

INPUT DATA
Process Type: {process_type}
Stages: {stages}

OUTPUT
JSON: {{
    "process_type": "{process_type}",
    "stages": [
        {{
            "stage_number": 1,
            "title": "string",
            "description": "string",
            "environment_details": ["string"],
            "camera_movement": "string"
        }}
    ],
    "estimated_total_duration_sec": 0
}}
"""
        res = await ai_client.generate(prompt=prompt, response_format={"type": "json_object"})
        return res if isinstance(res, dict) else {}

    async def generate_scenes(self, stages: list[dict[str, Any]]) -> list[str]:
        video_urls = []
        for stage in stages:
            prompt = f"{stage.get('title')}: {stage.get('description')} Camera: {stage.get('camera_movement')}"
            url = await ai_client.generate_video(prompt=prompt, text="")
            if url:
                video_urls.append(url)
        return video_urls

    async def assemble_final(self, video_urls: list[str]) -> str | None:
        if not video_urls:
            return None
            
        import os
        import asyncio
        import tempfile
        import httpx
        
        tmpdir = tempfile.mkdtemp()
        list_file_path = os.path.join(tmpdir, "list.txt")
        out_file_path = os.path.join(tmpdir, "output.mp4")
        
        try:
            async with httpx.AsyncClient() as client:
                for i, url in enumerate(video_urls):
                    if url.startswith("http"):
                        resp = await client.get(url)
                        resp.raise_for_status()
                        local_path = os.path.join(tmpdir, f"clip_{i}.mp4")
                        with open(local_path, "wb") as f:
                            f.write(resp.content)
                    else:
                        # Assuming it's already a mock id or local path, for simplicity we skip or create mock
                        local_path = os.path.join(tmpdir, f"clip_{i}.mp4")
                        with open(local_path, "wb") as f:
                            f.write(b"mock video content")
            
            with open(list_file_path, "w") as f:
                for i in range(len(video_urls)):
                    f.write(f"file 'clip_{i}.mp4'\n")
                    
            proc = await asyncio.create_subprocess_shell(
                f"ffmpeg -y -f concat -safe 0 -i list.txt -c copy output.mp4",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=tmpdir
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0 and os.path.exists(out_file_path):
                return out_file_path
            else:
                return None
        except Exception:
            return None

    async def execute(
        self,
        session: AsyncSession,
        input_data: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        project_id = input_data.get("project_id", (context or {}).get("project_id"))
        tenant_id = input_data.get("tenant_id", (context or {}).get("tenant_id"))
        project_data = input_data.get("project_data", "")

        await self.memory.get_company_profile(session, tenant_id, project_id)

        # 1. Analyze project
        process_type = await self.analyze_project(project_data)

        # 2. Build stages
        raw_stages = await self.build_stages(process_type, project_data)

        # 3. Plan camera
        camera_plan = await self.plan_camera(process_type, raw_stages)
        stages = camera_plan.get("stages", raw_stages)

        # 4. Generate scenes
        video_urls = await self.generate_scenes(stages)

        # 5. Assemble final
        final_video_path = await self.assemble_final(video_urls)

        stored_url = None
        if final_video_path and final_video_path.startswith("/tmp/"):
            import os
            import uuid
            if os.path.exists(final_video_path):
                with open(final_video_path, "rb") as f:
                    data = f.read()
                _, stored_url = await storage_client.store_bytes(
                    project_id=f"{tenant_id}/{project_id}/videos/timelapse",
                    file_name=f"final_{uuid.uuid4().hex}.mp4",
                    content_type="video/mp4",
                    data=data
                )
                os.remove(final_video_path)
        elif final_video_path and final_video_path.startswith("http"):
            stored_url = await storage_client.upload_from_url(final_video_path, f"{tenant_id}/{project_id}/videos/timelapse/")

        return {
            "video_url": stored_url,
            "camera_plan": camera_plan,
            "process_type": process_type
        }
