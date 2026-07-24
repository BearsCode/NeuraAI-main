import asyncio
import json

import httpx
from backend.app.core.configs import settings
from backend.app.core.exceptions import AIServiceError
from backend.app.db.enums import IntegrationPlatform
from backend.app.db.project import Project
from backend.app.infra.circuit_breaker import CircuitBreaker
from backend.app.infra.retry import async_retry


class AIClient:
    def __init__(self) -> None:
        self.breaker = CircuitBreaker(failure_threshold=5, reset_timeout_seconds=60)

    async def analyze_project(self, project: Project) -> dict[str, object]:
        if not settings.ai_api_key:
            channels = [platform.value for platform in IntegrationPlatform][:2]
            if project.social_links:
                channels = ["telegram", "vk"]
            services = ", ".join(project.services[:3]) if project.services else "core services"
            return {
                "business_analysis": [
                    f"{project.company_name} has a clear offer in {project.industry}.",
                    f"Main service cluster: {services}.",
                    f"Primary audience focus: {project.target_audience}.",
                ],
                "market_analysis": [
                    f"Demand for AI-driven marketing automation in {project.city} is growing.",
                    "SMB clients respond well to predictable content pipelines and visible ROI.",
                ],
                "competitor_analysis": [
                    "Most competitors split strategy, content, and analytics into separate tools.",
                    "Fast onboarding and autoposting can be used as differentiation points.",
                ],
                "positioning": (
                    f"{project.company_name} as an AI-powered outsourced marketing department "
                    f"for businesses in {project.industry}."
                ),
                "content_pillars": [
                    "expert content",
                    "client cases",
                    "service benefits",
                    "audience pain points",
                ],
                "channels": channels,
                "publishing_frequency": "5 posts per week",
                "recommendations": [
                    "Approve sales-focused posts manually and automate educational content.",
                    "Test weekday morning publishing windows for Telegram and VK first.",
                ],
                "optimization_mode": "manual_confirmation",
                "provider": "heuristic-fallback",
            }

        headers = {
            "x-api-key": settings.ai_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        system_prompt = (
            "You are a professional B2B marketing expert. You must analyze the business details and "
            "respond ONLY with a valid JSON object matching the requested schema. Do not include any "
            "markdown, formatting (like ```json), commentary, or text before or after the JSON."
        )

        user_content = (
            f"Analyze this project:\n"
            f"Company: {project.company_name}\n"
            f"Description: {project.business_description}\n"
            f"City: {project.city}\n"
            f"Industry: {project.industry}\n"
            f"Services: {project.services}\n"
            f"Target Audience: {project.target_audience}\n"
            f"Competitors: {project.competitors}\n"
            f"Features: {project.business_features}\n\n"
            f"Provide a JSON with the following structure:\n"
            f"{{\n"
            f"  \"business_analysis\": [\"string\", \"string\", ...],\n"
            f"  \"market_analysis\": [\"string\", \"string\", ...],\n"
            f"  \"competitor_analysis\": [\"string\", \"string\", ...],\n"
            f"  \"positioning\": \"string\",\n"
            f"  \"content_pillars\": [\"string\", \"string\", ...],\n"
            f"  \"channels\": [\"string\", \"string\", ...],\n"
            f"  \"publishing_frequency\": \"string\",\n"
            f"  \"recommendations\": [\"string\", \"string\", ...],\n"
            f"  \"optimization_mode\": \"manual_confirmation\"\n"
            f"}}"
        )

        payload = {
            "model": settings.ai_model,
            "max_tokens": 4000,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_content}
            ],
        }

        return await self.breaker.call(
            lambda: self._post_anthropic(payload, 60.0, "analyze_project")
        )

    async def _post_anthropic(self, payload: dict, timeout: float, _label: str = "") -> dict:
        headers = {
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await async_retry(
                lambda: client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload,
                ),
                retries=3, base_delay_seconds=1.0, max_delay_seconds=8.0,
            )
            if response.status_code != 200:
                raise AIServiceError(
                    message=f"Anthropic API error: {response.text}",
                    status_code=502,
                )
            data = response.json()
            text_content = data["content"][0]["text"].strip()
            try:
                parsed = json.loads(text_content)
                parsed["provider"] = "anthropic"
                return parsed
            except Exception:
                raise AIServiceError(
                    message="Failed to parse Anthropic JSON response",
                    status_code=500,
                )

    async def generate_post_text(self, project: Project, topic: str, platform: str) -> str:
        if not settings.ai_api_key:
            return (
                f"{project.company_name}: {topic or 'AI marketing update'} "
                f"tailored for {project.target_audience} on {platform}."
            )

        headers = {
            "x-api-key": settings.ai_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        prompt = (
            f"Generate a professional, high-quality social media post for {platform} for the company {project.company_name} "
            f"in the {project.industry} industry.\n"
            f"Company Description: {project.business_description}\n"
            f"Target Audience: {project.target_audience}\n"
            f"Topic: {topic}\n\n"
            f"Respond ONLY with the post text caption. Do not include any HTML, markdown, formatting, or commentary."
        )

        payload = {
            "model": settings.ai_model,
            "max_tokens": 2000,
            "messages": [
                {"role": "user", "content": prompt}
            ],
        }

        result = await self.breaker.call(
            lambda: self._post_anthropic_text(payload, 60.0)
        )
        return result

    async def _post_anthropic_text(self, payload: dict, timeout: float) -> str:
        headers = {
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await async_retry(
                lambda: client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload,
                ),
                retries=3, base_delay_seconds=1.0, max_delay_seconds=8.0,
            )
            if response.status_code != 200:
                raise AIServiceError(
                    message=f"Anthropic API error: {response.text}",
                    status_code=502,
                )
            data = response.json()
            return data["content"][0]["text"].strip()

    async def generate_image(self, prompt: str) -> str:
        if not settings.openai_api_key:
            return f"https://via.placeholder.com/1024x1024.png?text={prompt[:50]}"

        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": settings.dalle_model,
            "prompt": prompt,
            "n": 1,
            "size": settings.dalle_image_size,
        }

        return await self.breaker.call(
            lambda: self._post_openai_image(payload, headers, 90.0)
        )

    async def _post_openai_image(self, payload: dict, headers: dict, timeout: float) -> str:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await async_retry(
                lambda: client.post(
                    "https://api.openai.com/v1/images/generations",
                    headers=headers,
                    json=payload,
                ),
                retries=3, base_delay_seconds=1.0, max_delay_seconds=8.0,
            )
            if response.status_code != 200:
                raise AIServiceError(
                    message=f"OpenAI API error: {response.text}",
                    status_code=502,
                )
            data = response.json()
            return data["data"][0]["url"]

    async def generate(
        self,
        prompt: str,
        response_format: dict | None = None,
        system_prompt: str | None = None,
        images: list[str] | None = None,
    ) -> dict | str:
        if images and settings.openai_api_key:
            headers = {
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            }
            content = [{"type": "text", "text": prompt}]
            for img in images:
                content.append({"type": "image_url", "image_url": {"url": img}})
                
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": content})
            
            payload = {
                "model": "gpt-4o",
                "messages": messages,
                "max_tokens": 4000,
            }
            if response_format and response_format.get("type") == "json_object":
                payload["response_format"] = {"type": "json_object"}
                
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"OpenAI API error: {response.text}",
                    )
                data = response.json()
                text_content = data["choices"][0]["message"]["content"].strip()
                if response_format and response_format.get("type") == "json_object":
                    try:
                        return json.loads(text_content)
                    except json.JSONDecodeError:
                        return {"raw_text": text_content}
                return text_content

        if not settings.ai_api_key:
            return {"text": f"Mock response: {prompt[:100]}..."}

        headers = {
            "x-api-key": settings.ai_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        system = system_prompt or (
            "You are a professional B2B marketing AI assistant. "
            "Respond with valid JSON when requested. Be concise and accurate."
        )

        payload = {
            "model": settings.ai_model,
            "max_tokens": 4000,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        }

        return await self.breaker.call(
            lambda: self._post_anthropic_generic(payload, response_format, 120.0)
        )

    async def _post_anthropic_generic(self, payload: dict, response_format: dict | None, timeout: float) -> dict | str:
        headers = {
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await async_retry(
                lambda: client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload,
                ),
                retries=3, base_delay_seconds=1.0, max_delay_seconds=8.0,
            )
            if response.status_code != 200:
                raise AIServiceError(
                    message=f"Anthropic API error: {response.text}",
                    status_code=502,
                )
            data = response.json()
            text_content = data["content"][0]["text"].strip()
            if response_format and response_format.get("type") == "json_object":
                try:
                    return json.loads(text_content)
                except json.JSONDecodeError:
                    return {"raw_text": text_content}
            return text_content

    async def generate_talking_head(
        self, avatar_id: str, text: str, duration: int = 30
    ) -> str:
        heygen_cfg = settings.avatar.heygen
        if not heygen_cfg.api_key:
            return f"https://via.placeholder.com/1024x1024.png?text=talking+head+{avatar_id[:8]}"

        headers = {
            "X-Api-Key": heygen_cfg.api_key.get_secret_value(),
            "Content-Type": "application/json",
        }
        payload = {
            "avatar_id": avatar_id,
            "input_text": text,
            "voice_id": "2b6c0a4c6e3e4b3e8f4c6a7d8e9f0a1b",
            "caption": True,
            "style": "natural",
            "background": {"type": "solid", "color": "#FFFFFF"},
        }

        video_id = await self.breaker.call(
            lambda: self._post_heygen(payload, headers, heygen_cfg.base_url)
        )

        for attempt in range(30):
            await asyncio.sleep(10)
            status_response = await self._get_heygen_status(headers, heygen_cfg.base_url, video_id)
            if status_response is None:
                continue
            status_data = status_response
            video_data = status_data.get("data", {})
            if video_data.get("status") == "completed":
                video_url = video_data.get("video_url", "")
                if video_url:
                    return video_url
            elif video_data.get("status") == "failed":
                raise AIServiceError(
                    message=f"HeyGen video generation failed: {video_data.get('error', 'unknown')}",
                    status_code=502,
                )

        raise AIServiceError(
            message="HeyGen video generation timed out after 5 minutes",
            status_code=504,
        )

    async def _post_heygen(self, payload: dict, headers: dict, base_url: str) -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await async_retry(
                lambda: client.post(
                    f"{base_url}/v2/video/generate",
                    headers=headers,
                    json=payload,
                ),
                retries=3, base_delay_seconds=1.0, max_delay_seconds=8.0,
            )
            if response.status_code != 200:
                raise AIServiceError(
                    message=f"HeyGen API error: {response.text}",
                    status_code=502,
                )
            data = response.json()
            video_id = data.get("data", {}).get("video_id", "")
            if not video_id:
                raise AIServiceError(
                    message="HeyGen returned no video_id",
                    status_code=502,
                )
            return video_id

    async def _get_heygen_status(self, headers: dict, base_url: str, video_id: str) -> dict | None:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                status_response = await client.get(
                    f"{base_url}/v2/video/{video_id}",
                    headers=headers,
                )
                if status_response.status_code != 200:
                    return None
                return status_response.json()
        except Exception:
            return None

    import warnings

    async def generate_video(self, prompt: str, text: str | None = None) -> str:
        warnings.warn(
            "ai_client.generate_video is deprecated. Use media_adapters for video generation.",
            DeprecationWarning,
            stacklevel=2,
        )
        if not settings.openai_api_key: # Using this as a dummy check for whether we have external API access
            return "https://example.com/video/generated.mp4"
            
        # Kling API skeleton (text-to-video)
        # In a real scenario, this would use a proper API key for Kling/Luma/Sora
        kling_api_key = getattr(settings, "kling_api_key", None)
        if kling_api_key:
            headers = {
                "Authorization": f"Bearer {kling_api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "kling-v1",
                "prompt": prompt,
                "duration": 5
            }
            async with httpx.AsyncClient(timeout=90.0) as client:
                try:
                    response = await client.post(
                        "https://api.klingai.com/v1/videos/generations",
                        headers=headers,
                        json=payload,
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return data.get("video_url", "https://example.com/video/generated.mp4")
                except Exception:
                    pass
                    
        return "https://example.com/video/generated.mp4"

    async def healthcheck(self) -> dict[str, str]:
        if not settings.ai_api_key or not settings.openai_api_key:
            return {
                "status": "degraded",
                "detail": "Missing AI_API_KEY or OPENAI_API_KEY",
            }
        return {
            "status": "ok",
            "ai_model": settings.ai_model,
            "openai_model": settings.openai_model,
            "dalle_model": settings.dalle_model,
        }
