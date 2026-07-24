from pydantic import BaseModel


class AdminOverviewResponse(BaseModel):
    users_total: int
    projects_total: int
    active_subscriptions: int
    partners_total: int
    monthly_revenue: float


class AdminUserResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    projects_total: int


class AdminProjectResponse(BaseModel):
    project_id: str
    company_name: str
    owner_email: str
    industry: str
    strategy_status: str
