from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import execute_idempotent, get_current_user, require_idempotency_header
from backend.app.core.database import get_db_session
from backend.app.db.user import User
from backend.app.modules.billing.schemas import (
    ChangePlanRequest,
    CommissionResponse,
    PaymentResponse,
    SubscriptionPlanResponse,
    SubscriptionResponse,
)
from backend.app.schemas.promocode import PromocodePreviewRequest, PromocodePreviewResponse
from backend.app.modules.billing.service import BillingService

router = APIRouter(prefix="/billing", tags=["billing"])
service = BillingService()


@router.get("/plans", response_model=list[SubscriptionPlanResponse])
async def list_plans(
    session: AsyncSession = Depends(get_db_session),
) -> list[SubscriptionPlanResponse]:
    return await service.list_plans(session)


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SubscriptionResponse:
    return await service.get_subscription(session, current_user, x_tenant_id)


@router.post("/promocodes/preview", response_model=PromocodePreviewResponse)
async def preview_promocode(
    payload: PromocodePreviewRequest,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> PromocodePreviewResponse:
    return await service.preview_promocode(
        session=session,
        current_user=current_user,
        tenant_id=x_tenant_id,
        code=payload.code,
        plan_code=payload.plan_code,
    )


@router.patch("/subscription", response_model=SubscriptionResponse)
async def change_plan(
    payload: ChangePlanRequest,
    request: Request,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    idempotency_key: str = Depends(require_idempotency_header),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SubscriptionResponse:
    return await execute_idempotent(
        request=request,
        session=session,
        current_user=current_user,
        tenant_id=x_tenant_id,
        idempotency_key=idempotency_key,
        payload=payload,
        response_model=SubscriptionResponse,
        operation=lambda: service.change_plan(
            session,
            current_user,
            x_tenant_id,
            payload.plan_code,
            payload.promo_code,
        ),
    )


@router.get("/payments", response_model=list[PaymentResponse])
async def list_payments(
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[PaymentResponse]:
    return await service.list_payments(session, current_user, x_tenant_id)


@router.get("/commissions", response_model=list[CommissionResponse])
async def list_commissions(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[CommissionResponse]:
    return await service.list_commissions(session, current_user)


@router.post("/yookassa/webhook")
async def yookassa_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    payload = await request.json()
    return await service.handle_webhook(session, payload)


@router.post("/payments/{payment_id}/refund")
async def refund_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    # Additional auth checks should be done here to ensure only admin/owner can refund
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can refund payments")
    return await service.refund_payment(session, payment_id)
