import logging
import ssl
from pathlib import Path

import certifi
import httpx
from src.settings import TochkaSettings, AppSettings

logger = logging.getLogger(__name__)

# API Точки (enter.tochka.com) подписан корневым сертификатом Минцифры (Russian Trusted
# Root CA), которого нет в стандартном наборе certifi. Доверяем ему дополнительно к
# стандартным. Источник: https://gu-st.ru/content/lending/russian_trusted_root_ca_pem.crt
# SHA-256: D2:6D:2D:02:31:B7:C3:9F:92:CC:73:85:12:BA:54:10:35:19:E4:40:5D:68:B5:BD:70:3E:97:88:CA:8E:CF:31
# Действует до 27.02.2032.
_RUSSIAN_ROOT_CA = Path(__file__).resolve().parent.parent / "certs" / "russian_trusted_root_ca.pem"


def _tochka_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context(cafile=certifi.where())
    ctx.load_verify_locations(cafile=str(_RUSSIAN_ROOT_CA))
    return ctx


# Время жизни платёжной ссылки. Короткое, чтобы брошенные неоплаченные заказы
# быстро получали от Точки статус EXPIRED и автоматически отменялись.
PAYMENT_LINK_TTL_MINUTES = 60


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
            verify=_tochka_ssl_context(),
            # Не брать прокси из окружения (HTTP_PROXY/ALL_PROXY): запросы к российскому
            # банку не должны идти через VPN/прокси разработчика, а схему socks:// httpx
            # без доп. зависимостей вообще не поддерживает.
            trust_env=False,
        )

    def create_payment(
            self,
            amount: int,
            payment_token: str,
            purpose: str = "Оплата заказа на стирку",
    ) -> dict:
        """Создание ссылки на оплату через Точка Банк."""
        return_url = f"{self._frontend_url}/?payment_token={payment_token}"
        payload = {
            "Data": {
                "customerCode": self.customer_code,
                "amount": f"{amount}.00",
                "purpose": purpose,
                "redirectUrl": return_url,
                "failRedirectUrl": return_url,
                "paymentMode": [
                    "sbp",
                    "card"
                ],
                "saveCard": True,
                "ttl": PAYMENT_LINK_TTL_MINUTES,
                "paymentLinkId": payment_token,
            }
        }
        # response = self.client.post("payments_with_receipt", json=payload)
        # https://chat.deepseek.com/a/chat/s/8385ad91-b26e-4b1b-a1a3-43415a0052ea
        response = self.client.post("payments", json=payload)
        response.raise_for_status()
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
