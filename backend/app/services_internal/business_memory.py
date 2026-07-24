from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.analytics_snapshot import AnalyticsSnapshot
from backend.app.db.business_memory import BusinessMemory
from backend.app.db.content_item import ContentItem
from backend.app.db.content_plan import ContentPlan
from backend.app.db.internship_state import InternshipState
from backend.app.db.project import Project
from backend.app.db.project_strategy import ProjectStrategy
from backend.app.db.publication import Publication
from backend.app.db.publication_target import PublicationTarget
from backend.app.db.retail_product import RetailProduct
from backend.app.db.training_signal import TrainingSignal


class BusinessMemoryService:
    async def get_company_profile(self, session: AsyncSession, tenant_id: str, project_id: str) -> dict:
        project = await session.scalar(
            select(Project).where(Project.id == project_id, Project.tenant_id == tenant_id)
        )
        if not project:
            return {}

        strategy = await session.scalar(
            select(ProjectStrategy).where(
                ProjectStrategy.project_id == project_id,
                ProjectStrategy.tenant_id == tenant_id,
            )
        )

        memories = (
            await session.scalars(
                select(BusinessMemory).where(
                    BusinessMemory.tenant_id == tenant_id,
                    BusinessMemory.project_id == project_id,
                    BusinessMemory.memory_type == "company_profile",
                    BusinessMemory.is_active,
                )
            )
        ).all()

        brand_memories = next(
            (m.content or {} for m in memories if m.title == "brand_voice"),
            {},
        )
        restriction_memories = next(
            (m.content or {} for m in memories if m.title == "content_restrictions"),
            {},
        )

        profile = {
            "company_name": project.company_name,
            "company_description": project.business_description,
            "company_niche": project.industry,
            "target_audience": project.target_audience,
            "brand_voice": brand_memories.get("voice", ""),
            "content_restrictions": restriction_memories.get("restrictions", ""),
            "strategy": {
                "positioning": strategy.positioning if strategy else "",
                "content_pillars": strategy.content_pillars if strategy else [],
                "channels": strategy.channels if strategy else [],
                "publishing_frequency": strategy.publishing_frequency if strategy else "3 posts per week",
                "recommendations": strategy.recommendations if strategy else [],
            } if strategy else None,
            "additional_context": {m.title: m.content for m in memories},
        }
        return profile

    async def get_preference_model(self, session: AsyncSession, tenant_id: str, project_id: str) -> dict:
        signals = (
            await session.scalars(
                select(TrainingSignal)
                .where(
                    TrainingSignal.tenant_id == tenant_id,
                    TrainingSignal.project_id == project_id,
                )
                .order_by(desc(TrainingSignal.created_at))
                .limit(500)
            )
        ).all()

        internship = await session.scalar(
            select(InternshipState).where(
                InternshipState.tenant_id == tenant_id,
                InternshipState.project_id == project_id,
            )
        )

        weights: dict[str, float] = {}
        topic_affinity: dict[str, float] = {}
        format_preference: dict[str, float] = {}
        tone_preference: dict[str, float] = {}

        for signal in signals:
            action = signal.action
            weight = signal.signal_weight
            context = signal.context or {}

            topic = context.get("topic")
            fmt = context.get("format")
            tone = context.get("tone")

            if action == "approved":
                delta = 1.0 * weight
            elif action == "approved_with_edits":
                delta = 0.5 * weight
            elif action == "rejected_with_comment":
                delta = -3.0 * weight
            elif action == "rejected":
                delta = -1.0 * weight
            elif action == "deleted_after_publish":
                delta = -2.0 * weight
            elif action == "marked_as_best":
                delta = 2.5 * weight
            else:
                delta = 0.0

            if topic:
                topic_affinity[topic] = topic_affinity.get(topic, 0.0) + delta
            if fmt:
                format_preference[fmt] = format_preference.get(fmt, 0.0) + delta
            if tone:
                tone_preference[tone] = tone_preference.get(tone, 0.0) + delta

        return {
            "weights": weights,
            "topic_affinity": topic_affinity,
            "format_preference": format_preference,
            "tone_preference": tone_preference,
            "total_signals": len(signals),
            "internship_completed": internship.stage == "completed" if internship else False,
            "preference_model": internship.preference_model if internship else {},
        }

    async def get_publication_history(
        self, session: AsyncSession, tenant_id: str, project_id: str, limit: int = 100
    ) -> list[dict]:
        pubs = (
            await session.scalars(
                select(Publication)
                .where(
                    Publication.tenant_id == tenant_id,
                    Publication.project_id == project_id,
                )
                .order_by(desc(Publication.scheduled_at))
                .limit(limit)
            )
        ).all()

        results = []
        for p in pubs:
            target = await session.scalar(
                select(PublicationTarget).where(
                    PublicationTarget.publication_id == p.id
                )
            )
            content_item = None
            if p.content_item_id:
                content_item = await session.scalar(
                    select(ContentItem).where(ContentItem.id == p.content_item_id)
                )
            results.append({
                "id": p.id,
                "content_item_id": p.content_item_id,
                "platform": p.platform,
                "status": p.status,
                "scheduled_at": p.scheduled_at.isoformat() if p.scheduled_at else None,
                "published_at": p.published_at.isoformat() if p.published_at else None,
                "external_url": p.external_url,
                "external_post_id": p.external_post_id or (target.external_post_id if target else None),
                "content_type": p.content_type.value if p.content_type else (
                    content_item.content_type.value if content_item else None
                ),
            })

        return results

    async def get_analytics(
        self, session: AsyncSession, tenant_id: str, project_id: str, days: int = 30
    ) -> dict:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        snapshots = (
            await session.scalars(
                select(AnalyticsSnapshot)
                .where(
                    AnalyticsSnapshot.tenant_id == tenant_id,
                    AnalyticsSnapshot.project_id == project_id,
                    AnalyticsSnapshot.created_at >= cutoff,
                )
                .order_by(desc(AnalyticsSnapshot.created_at))
                .limit(90)
            )
        ).all()

        total_reach = sum(s.reach or 0 for s in snapshots)
        total_likes = sum(s.likes or 0 for s in snapshots)
        total_comments = sum(s.comments or 0 for s in snapshots)
        total_saves = sum(s.saves or 0 for s in snapshots)

        return {
            "total_posts": len(snapshots),
            "total_reach": total_reach,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_clicks": total_saves,
            "avg_engagement_rate": ((total_likes + total_comments) / total_reach * 100) if total_reach > 0 else 0.0,
            "snapshots": [
                {
                    "id": s.id,
                    "data": s.raw_metrics,
                    "created_at": s.created_at.isoformat(),
                }
                for s in snapshots
            ],
        }

    async def get_topic_model(self, session: AsyncSession, tenant_id: str, project_id: str) -> dict:
        signals = (
            await session.scalars(
                select(TrainingSignal)
                .where(
                    TrainingSignal.tenant_id == tenant_id,
                    TrainingSignal.project_id == project_id,
                    TrainingSignal.applied,
                )
                .order_by(desc(TrainingSignal.created_at))
                .limit(200)
            )
        ).all()

        topic_engagement: dict[str, dict[str, Any]] = {}
        for signal in signals:
            context = signal.context or {}
            topic = context.get("topic")
            if not topic:
                continue
            if topic not in topic_engagement:
                topic_engagement[topic] = {"count": 0, "approved": 0, "rejected": 0, "total_weight": 0.0}
            topic_engagement[topic]["count"] += 1
            topic_engagement[topic]["total_weight"] += signal.signal_weight
            if signal.action in ("approved", "approved_with_edits", "marked_as_best"):
                topic_engagement[topic]["approved"] += 1
            elif signal.action in ("rejected", "deleted_after_publish"):
                topic_engagement[topic]["rejected"] += 1

        sorted_topics = sorted(
            topic_engagement.items(),
            key=lambda x: x[1]["approved"] / max(x[1]["count"], 1),
            reverse=True,
        )

        return {
            "topics": [
                {
                    "topic": t,
                    "stats": s,
                    "success_rate": s["approved"] / max(s["count"], 1) * 100,
                }
                for t, s in sorted_topics
            ],
            "successful_topics": [t for t, s in sorted_topics if s["approved"] / max(s["count"], 1) >= 0.7],
        }

    async def get_retail_catalog(
        self, session: AsyncSession, tenant_id: str, project_id: str
    ) -> dict:
        products = (
            await session.scalars(
                select(RetailProduct)
                .where(
                    RetailProduct.tenant_id == tenant_id,
                    RetailProduct.project_id == project_id,
                    RetailProduct.is_active,
                )
                .order_by(desc(RetailProduct.updated_at))
                .limit(500)
            )
        ).all()

        return {
            "total_products": len(products),
            "products": [
                {
                    "id": p.id,
                    "external_id": p.external_id,
                    "name": p.name,
                    "price": p.price,
                    "old_price": p.old_price,
                    "category": p.category,
                    "stock_quantity": p.stock_quantity,
                    "is_on_sale": p.is_on_sale,
                    "image_urls": p.image_urls,
                    "source_system": p.source_system,
                }
                for p in products
            ],
            "categories": list({p.category for p in products if p.category}),
            "on_sale": [p for p in products if p.is_on_sale],
            "out_of_stock": [p for p in products if p.stock_quantity is not None and p.stock_quantity <= 0],
        }

    async def get_content_plan(self, session: AsyncSession, tenant_id: str, project_id: str) -> dict:
        plans = (
            await session.scalars(
                select(ContentPlan)
                .where(
                    ContentPlan.tenant_id == tenant_id,
                    ContentPlan.project_id == project_id,
                )
                .order_by(desc(ContentPlan.created_at))
                .limit(5)
            )
        ).all()

        return {
            "plans": [
                {
                    "id": p.id,
                    "plan_data": p.plan_data,
                    "status": p.status,
                    "created_at": p.created_at.isoformat(),
                }
                for p in plans
            ],
        }

    async def store_memory(
        self,
        session: AsyncSession,
        tenant_id: str,
        project_id: str,
        memory_type: str,
        title: str,
        content: dict,
        source: str | None = None,
        confidence: float | None = None,
    ) -> BusinessMemory:
        memory = BusinessMemory(
            tenant_id=tenant_id,
            project_id=project_id,
            memory_type=memory_type,
            title=title,
            content=content,
            source=source,
            confidence=confidence,
        )
        session.add(memory)
        await session.flush()
        return memory

    async def get_full_context(self, session: AsyncSession, tenant_id: str, project_id: str) -> dict:
        profile = await self.get_company_profile(session, tenant_id, project_id)
        preferences = await self.get_preference_model(session, tenant_id, project_id)
        analytics = await self.get_analytics(session, tenant_id, project_id, days=30)
        topics = await self.get_topic_model(session, tenant_id, project_id)
        content_plan = await self.get_content_plan(session, tenant_id, project_id)
        catalog = await self.get_retail_catalog(session, tenant_id, project_id)
        history = await self.get_publication_history(session, tenant_id, project_id, limit=20)

        return {
            "company_profile": profile,
            "preferences": preferences,
            "analytics": analytics,
            "topic_model": topics,
            "content_plan": content_plan,
            "retail_catalog": catalog,
            "publication_history": history,
        }
