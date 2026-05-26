import logging

import httpx
from src.settings import TochkaSettings, AppSettings
from icecream import ic

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self):
        settings = TochkaSettings()
        app_settings = AppSettings()

        self.customer_code = settings.TOCHKA_CUSTOMER_CODE_BUISNESS
        domain = app_settings.DOMAIN
        self._frontend_url = f"https://{domain}" if "localhost" not in domain else f"http://{domain}"

        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.TOCHKA_TOKEN}'
        }

        self.client = httpx.Client(
            base_url='https://enter.tochka.com/uapi/acquiring/v1.0/',
            headers=headers,
            timeout=30.0,
        )

    def create_payment(
            self,
            amount: int,
            payment_token: str,
            purpose: str = "Оплата заказа на стирку",
    ) -> dict:
        """Создание ссылки на оплату через Точка Банк."""
        return_url = f"{self._frontend_url}/order?payment_token={payment_token}"
        payload = {
            "Data": {
                "customerCode": self.customer_code,
                "amount": "1.00",
                # "amount": f"{amount}.00",
                "purpose": purpose,
                "redirectUrl": return_url,
                "failRedirectUrl": return_url,
                "paymentMode": [
                    "sbp",
                    "card"
                ],
                "saveCard": True,
                "ttl": 10080,
                "paymentLinkId": payment_token,
            }
        }
        ic(payload)
        response = self.client.post("payments", json=payload)
        response.raise_for_status()
        ic(response.url)
        data = response.json().get("Data", {})
        return {
            "operation_id": data["operationId"],
            "payment_link": data.get("paymentLink"),
        }

    def get_payment(self, operation_id: str) -> dict:
        """Получение информации о платеже по operationId."""
        response = self.client.get(f"payments/{operation_id}")
        response.raise_for_status()
        return response.json()
