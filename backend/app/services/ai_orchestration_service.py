from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, time, timedelta
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.content_item import ContentItem
from backend.app.db.content_plan import ContentPlan
from backend.app.db.enums import ContentSourceMode, ContentStatus, ContentType, IntegrationPlatform
from backend.app.db.project import Project
from backend.app.db.project_strategy import ProjectStrategy
from backend.app.db.prompt_template import PromptTemplate
from backend.app.integrations.ai_adapters import AIGenerateRequest, build_ai_adapter


class GeneratedStrategyPayload(BaseModel):
    """Structured strategy output expected from the LLM."""

    model_config = ConfigDict(extra="forbid")

    business_analysis: list[str] = Field(min_length=2)
    market_analysis: list[str] = Field(min_length=2)
    competitor_analysis: list[str] = Field(min_length=2)
    positioning: str = Field(min_length=20)
    content_pillars: list[str] = Field(min_length=3)
    channels: list[str] = Field(min_length=1)
    publishing_frequency: str = Field(min_length=3)
    recommendations: list[str] = Field(min_length=2)
    optimization_mode: Literal["manual_confirmation", "auto_publish"] = "manual_confirmation"


class GeneratedContentPlanItemPayload(BaseModel):
    """Single day of the generated content plan."""

    model_config = ConfigDict(extra="forbid")

    day_number: int = Field(ge=1, le=90)
    title: str = Field(min_length=5, max_length=255)
    angle: str = Field(min_length=10)
    platform: Literal["telegram", "vk"]
    content_type: Literal["post", "carousel", "story", "video"]
    media_type: Literal["text_only", "image", "video", "carousel"]
    caption: str = Field(min_length=20)
    call_to_action: str = Field(min_length=3, max_length=255)
    publish_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    image_prompt: str | None = None


class GeneratedContentPlanPayload(BaseModel):
    """Structured content plan output expected from the LLM."""

    model_config = ConfigDict(extra="forbid")

    plan_summary: str = Field(min_length=20)
    posts: list[GeneratedContentPlanItemPayload] = Field(min_length=7, max_length=90)


class AIOrchestrationService:
    """Orchestrates prompt loading, LLM invocation, validation, and persistence."""

    async def generate_strategy(self, session: AsyncSession, project: Project) -> ProjectStrategy:
        """Generate and persist a project strategy."""

        await self._ensure_default_templates(session)
        template = await self._get_active_template(session, "strategy_generation")
        payload = await self._invoke_model(
            task_type="strategy_generation",
            template=template,
            context=self._project_context(project),
            schema_model=GeneratedStrategyPayload,
        )

        strategy = await session.scalar(select(ProjectStrategy).where(ProjectStrategy.project_id == project.id))
        if strategy is None:
            strategy = ProjectStrategy(tenant_id=project.tenant_id, project_id=project.id)
            session.add(strategy)

        strategy.business_analysis = payload.business_analysis
        strategy.market_analysis = payload.market_analysis
        strategy.competitor_analysis = payload.competitor_analysis
        strategy.positioning = payload.positioning
        strategy.content_pillars = payload.content_pillars
        strategy.channels = payload.channels
        strategy.publishing_frequency = payload.publishing_frequency
        strategy.recommendations = payload.recommendations
        strategy.optimization_mode = payload.optimization_mode
        await session.flush()
        return strategy

    async def generate_content_plan(
        self,
        session: AsyncSession,
        project: Project,
        *,
        period_days: int,
        source_mode: str,
        platforms: list[str],
        content_types: list[str],
        version: int,
    ) -> tuple[ContentPlan, list[ContentItem]]:
        """Generate and persist a content plan for a project."""

        await self._ensure_default_templates(session)
        template = await self._get_active_template(session, "content_plan_generation")
        payload = await self._invoke_model(
            task_type="content_plan_generation",
            template=template,
            context={
                **self._project_context(project),
                "period_days": period_days,
                "source_mode": source_mode,
                "platforms": ", ".join(platforms or ["telegram", "vk"]),
                "content_types": ", ".join(content_types or ["post", "carousel"]),
            },
            schema_model=GeneratedContentPlanPayload,
        )

        plan = ContentPlan(
            tenant_id=project.tenant_id,
            project_id=project.id,
            period_days=period_days,
            source_mode=ContentSourceMode(source_mode),
            status="generated",
            version=version,
        )
        session.add(plan)
        await session.flush()

        items: list[ContentItem] = []
        base_date = datetime.now(UTC).date()
        for post in payload.posts[:period_days]:
            publish_hour, publish_minute = [int(part) for part in post.publish_time.split(":", maxsplit=1)]
            item = ContentItem(
                tenant_id=project.tenant_id,
                project_id=project.id,
                plan_id=plan.id,
                platform=IntegrationPlatform(post.platform),
                content_type=ContentType(post.content_type),
                publish_date=base_date + timedelta(days=post.day_number - 1),
                publish_time=time(hour=publish_hour, minute=publish_minute),
                status=ContentStatus.GENERATED,
                title=post.title,
                text=post.caption,
                metadata_json={
                    "day_number": post.day_number,
                    "angle": post.angle,
                    "call_to_action": post.call_to_action,
                    "media_type": post.media_type,
                    "image_prompt": post.image_prompt,
                    "plan_summary": payload.plan_summary,
                },
            )
            session.add(item)
            items.append(item)

        await session.flush()
        return plan, items

    async def _invoke_model(
        self,
        *,
        task_type: str,
        template: PromptTemplate,
        context: dict[str, Any],
        schema_model: type[BaseModel],
    ) -> BaseModel:
        adapter = build_ai_adapter()
        raw_payload = await adapter.generate(
            AIGenerateRequest(
                task_type=task_type,
                context={
                    **context,
                    "system_prompt": template.system_prompt,
                    "user_prompt": self._render_prompt(template.user_prompt_template, context),
                    "response_schema": template.response_schema,
                },
            )
        )
        return schema_model.model_validate(raw_payload)

    async def _ensure_default_templates(self, session: AsyncSession) -> None:
        existing = await session.scalar(select(PromptTemplate.id).limit(1))
        if existing is not None:
            return

        for template in self._default_templates():
            session.add(template)
        await session.flush()

    async def _get_active_template(self, session: AsyncSession, task_type: str) -> PromptTemplate:
        template = await session.scalar(
            select(PromptTemplate)
            .where(PromptTemplate.task_type == task_type, PromptTemplate.is_active.is_(True))
            .order_by(PromptTemplate.version.desc())
        )
        if template is None:
            raise ValueError(f"Prompt template is not configured for task {task_type}")
        return template

    def _render_prompt(self, template: str, context: dict[str, Any]) -> str:
        safe_context = defaultdict(str, context)
        return template.format_map(safe_context)

    def _project_context(self, project: Project) -> dict[str, Any]:
        return {
            "tenant_id": project.tenant_id,
            "project_id": project.id,
            "company_name": project.company_name,
            "business_description": project.business_description,
            "city": project.city,
            "industry": project.industry,
            "services": ", ".join(project.services or []),
            "website": project.website or "",
            "social_links": ", ".join(project.social_links or []),
            "target_audience": project.target_audience,
            "competitors": ", ".join(project.competitors or []),
            "business_features": ", ".join(project.business_features or []),
        }

    def _default_templates(self) -> list[PromptTemplate]:
        strategy_schema = GeneratedStrategyPayload.model_json_schema(mode="serialization")
        content_plan_schema = GeneratedContentPlanPayload.model_json_schema(mode="serialization")
        return [
            PromptTemplate(
                name="Default strategy generation",
                task_type="strategy_generation",
                version=1,
                system_prompt=(
                    "You are a senior B2B marketing strategist. "
                    "Return only valid JSON strictly matching the response schema."
                ),
                user_prompt_template=(
                    "Generate a 30-day growth strategy for {company_name}.\n"
                    "Industry: {industry}\n"
                    "City: {city}\n"
                    "Business description: {business_description}\n"
                    "Services: {services}\n"
                    "Target audience: {target_audience}\n"
                    "Competitors: {competitors}\n"
                    "Business features: {business_features}\n"
                ),
                response_schema=strategy_schema,
                is_active=True,
            ),
            PromptTemplate(
                name="Default content plan generation",
                task_type="content_plan_generation",
                version=1,
                system_prompt=(
                    "You are a principal content strategist for B2B brands. "
                    "Return only valid JSON strictly matching the response schema."
                ),
                user_prompt_template=(
                    "Create a content plan for {company_name}.\n"
                    "Industry: {industry}\n"
                    "Description: {business_description}\n"
                    "Audience: {target_audience}\n"
                    "Platforms: {platforms}\n"
                    "Content types: {content_types}\n"
                    "Planning horizon: {period_days} days\n"
                    "Source mode: {source_mode}\n"
                    "Competitors: {competitors}\n"
                    "Business features: {business_features}\n"
                ),
                response_schema=content_plan_schema,
                is_active=True,
            ),
        ]
