import uuid
import httpx
from fastapi import HTTPException
from backend.app.core.configs import settings

class YooKassaClient:
    BASE_URL = "https://api.yookassa.ru/v3"

    def __init__(self):
        if not settings.billing.yookassa.is_configured:
            raise ValueError("YooKassa is not configured")
        self.shop_id = settings.billing.yookassa.shop_id
        self.secret_key = settings.billing.yookassa.secret_key.get_secret_value()

    def _get_auth(self) -> tuple[str, str]:
        return (self.shop_id, self.secret_key)

    async def create_payment(
        self,
        amount: float,
        currency: str,
        description: str,
        return_url: str,
        customer_email: str,
        metadata: dict | None = None,
    ) -> dict:
        url = f"{self.BASE_URL}/payments"
        headers = {"Idempotence-Key": str(uuid.uuid4())}
        
        # OFD Receipt data
        receipt = {
            "customer": {"email": customer_email},
            "items": [
                {
                    "description": description,
                    "quantity": "1.00",
                    "amount": {"value": f"{amount:.2f}", "currency": currency},
                    "vat_code": 1, # 1 - без НДС
                    "payment_mode": "full_prepayment",
                    "payment_subject": "service",
                }
            ]
        }

        payload = {
            "amount": {"value": f"{amount:.2f}", "currency": currency},
            "capture": True,
            "confirmation": {"type": "redirect", "return_url": return_url},
            "description": description,
            "receipt": receipt,
        }
        if metadata:
            payload["metadata"] = metadata

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, json=payload, headers=headers, auth=self._get_auth(), timeout=10.0
            )
            response.raise_for_status()
            return response.json()

    async def refund_payment(self, payment_id: str, amount: float, currency: str, description: str) -> dict:
        url = f"{self.BASE_URL}/refunds"
        headers = {"Idempotence-Key": str(uuid.uuid4())}
        payload = {
            "payment_id": payment_id,
            "amount": {"value": f"{amount:.2f}", "currency": currency},
            "description": description,
            "receipt": {
                "items": [
                    {
                        "description": description,
                        "quantity": "1.00",
                        "amount": {"value": f"{amount:.2f}", "currency": currency},
                        "vat_code": 1,
                        "payment_mode": "full_prepayment",
                        "payment_subject": "service",
                    }
                ]
            }
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, json=payload, headers=headers, auth=self._get_auth(), timeout=10.0
            )
            response.raise_for_status()
            return response.json()
