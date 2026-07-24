from backend.app.db.enums import PublicationStatus
from backend.app.db.user import User
from backend.app.schemas.dashboard import (
    DashboardCalendarItem,
    DashboardMetric,
    DashboardResponse,
)
from backend.app.services.project_service import ensure_project_access


class DashboardService:
    async def get_dashboard(self, session, current_user: User, project_id: str) -> DashboardResponse:
        project = await ensure_project_access(session, project_id, current_user)
        connected_socials = sum(1 for item in project.integrations if item.autoposting_enabled)
        pending_approval = sum(
            1 for item in project.publications if item.status == PublicationStatus.PENDING_APPROVAL
        )
        ai_recommendations = project.strategy.recommendations if project.strategy else []
        calendar = [
            DashboardCalendarItem(
                publication_id=publication.id,
                platform=publication.platform.value,
                scheduled_at=publication.scheduled_at,
                status=publication.status.value,
            )
            for publication in sorted(project.publications, key=lambda item: item.scheduled_at)[:10]
        ]
        return DashboardResponse(
            project_id=project.id,
            metrics=[
                DashboardMetric(label="publications_total", value=len(project.publications)),
                DashboardMetric(label="connected_socials", value=connected_socials),
                DashboardMetric(label="content_items_total", value=len(project.content_items)),
                DashboardMetric(label="pending_approval", value=pending_approval),
            ],
            ai_recommendations=ai_recommendations[:3]
            or [
                "Generate the first strategy to unlock AI recommendations.",
            ],
            content_calendar=calendar,
            strategy_state=project.strategy_status.value,
        )
