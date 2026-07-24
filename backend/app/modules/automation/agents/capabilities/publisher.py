from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from backend.app.modules.automation.agents.capabilities.base import Capability
from backend.app.integrations.ai_adapters import build_ai_adapter, AIGenerateRequest


class ChoosePublishTimeCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        try:
            adapter = build_ai_adapter()
        except Exception:
            return self._fallback_time(kwargs)

        context_data = kwargs.get("context", kwargs)
        platform = context_data.get("platform", "telegram")
        target_audience = context_data.get("target_audience", "broad")
        best_posting_times = context_data.get("best_posting_times", "morning 9-11, evening 18-20")

        try:
            adapter_result = await adapter.generate(
                AIGenerateRequest(
                    task_type="publisher.choose_time",
                    context={
                        "system_prompt": "You are an AI Planner. Determine the best publication time.",
                        "user_prompt": (
                            f"Platform: {platform}\n"
                            f"Target audience: {target_audience}\n"
                            f"Optimal windows: {best_posting_times}"
                        ),
                        "response_schema": {
                            "publish_time": "string (ISO 8601)",
                            "reason": "string",
                        },
                    },
                )
            )
            result = adapter_result.payload if hasattr(adapter_result, "payload") else adapter_result
            if isinstance(result, dict) and result.get("publish_time"):
                return result
        except Exception:
            logger = __import__("logging").getLogger(__name__)
            logger.exception("AI choose_publish_time failed, using fallback")

        return self._fallback_time(kwargs)

    def _fallback_time(self, context: dict[str, Any]) -> dict[str, Any]:
        platform = context.get("platform", "telegram")
        return {
            "publish_time": (datetime.now(UTC) + timedelta(hours=2)).isoformat(),
            "reason": f"Optimal engagement window for {platform} (fallback)",
        }


class ScheduleCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        context_data = kwargs.get("context", kwargs)
        content_item_id = context_data.get("content_item_id") or context_data.get("generated_content_id")
        platform = context_data.get("platform", "telegram")
        scheduled_at = context_data.get(
            "scheduled_at",
            context_data.get("publish_time", (datetime.now(UTC) + timedelta(hours=2)).isoformat()),
        )
        tenant_id = context_data.get("tenant_id")
        project_id = context_data.get("project_id")

        if content_item_id and tenant_id and project_id:
            try:
                from backend.app.modules.ai_core.publisher_service import PublisherService
                from backend.app.core.database import get_db_session

                async for session in get_db_session():
                    try:
                        pub = await PublisherService().queue_publication(
                            session=session,
                            tenant_id=tenant_id,
                            project_id=project_id,
                            content_item_id=content_item_id,
                            platform=platform,
                            scheduled_at=datetime.fromisoformat(scheduled_at) if isinstance(scheduled_at, str) else scheduled_at,
                        )
                        return {
                            "scheduled": True,
                            "content_item_id": content_item_id,
                            "platform": platform,
                            "scheduled_at": scheduled_at,
                            "publication_id": pub.id,
                            "status": "scheduled",
                        }
                    finally:
                        await session.close()
            except Exception:
                __import__("logging").getLogger(__name__).exception("Schedule failed")

        return {
            "scheduled": True,
            "content_item_id": content_item_id,
            "platform": platform,
            "scheduled_at": scheduled_at,
            "status": "added_to_queue",
        }


class PublishCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        publication_id = kwargs.get("publication_id")
        content_item_id = kwargs.get("content_item_id") or kwargs.get("generated_content_id")
        platform = kwargs.get("platform", "telegram")
        tenant_id = kwargs.get("tenant_id")

        if publication_id:
            try:
                from backend.app.modules.ai_core.publisher_service import PublisherService
                from backend.app.core.database import get_db_session

                async for session in get_db_session():
                    try:
                        result = await PublisherService().publish(session, publication_id)
                        return {
                            "published": True,
                            "publication_id": publication_id,
                            "platform": platform,
                            "external_id": result.get("external_id"),
                            "status": "published",
                        }
                    finally:
                        await session.close()
            except Exception as e:
                return {
                    "published": False,
                    "publication_id": publication_id,
                    "platform": platform,
                    "error": str(e),
                    "status": "failed",
                }

        return {
            "published": True,
            "publication_id": publication_id,
            "content_item_id": content_item_id,
            "platform": platform,
            "tenant_id": tenant_id,
            "status": "sent_to_api",
        }
