from pydantic import BaseModel


class PartnerDashboardResponse(BaseModel):
    referral_link: str
    referral_code: str
    total_referrals: int
    successful_payments_count: int
    total_commission: float
    available_balance: float
    commission_rate: float
