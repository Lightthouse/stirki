import logging
import ssl
from pathlib import Path

import certifi
import httpx
from src.services.pricing import OrderLine
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
        self.tax_system_code = settings.TOCHKA_TAX_SYSTEM_CODE
        self.merchant_id = settings.TOCHKA_MERCHANT_ID
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
            lines: list[OrderLine],
            payment_token: str,
            payment_link_id: str,
            order_number: str,
            email: str,
            client_name: str | None = None,
            purpose: str = "Оплата заказа на стирку",
    ) -> dict:
        """Создание ссылки на оплату с кассовым чеком (54-ФЗ) через Точка Банк.

        Чек уходит покупателю на `email`. Позиции чека — пакеты и вещи заказа,
        сумма платежа равна сумме позиций. Суммы — в рублях. Работаем без НДС.
        В название каждой позиции дописываем номер заказа: названия позиций печатаются
        в чеке всегда (54-ФЗ), так чек однозначно связывается с заказом в админке.
        """
        order_suffix = f", заказ {order_number}"
        return_url = f"{self._frontend_url}/?payment_token={payment_token}"
        client = {"email": email}
        if client_name:
            client["name"] = client_name
        data = {
            "customerCode": self.customer_code,
            "amount": sum(line.total for line in lines),
            "purpose": purpose,
            "redirectUrl": return_url,
            "failRedirectUrl": return_url,
            # Доступные способы — в GET /acquiring/v1.0/retailers, поле paymentModes.
            "paymentMode": [
                "sbp",
                "card",
                "tinkoff",
            ],
            "saveCard": True,
            "ttl": PAYMENT_LINK_TTL_MINUTES,
            # Номер заказа, который покупатель видит на странице оплаты (уникален навсегда).
            "paymentLinkId": payment_link_id,
            "Client": client,
            "Items": [
                {
                    # Лимит Точки — 256 символов; обрезаем описание, а не номер заказа.
                    "name": line.name[:256 - len(order_suffix)] + order_suffix,
                    "amount": line.unit_price,
                    "quantity": line.quantity,
                    "vatType": "none",
                    "paymentMethod": "full_payment",
                    "paymentObject": "service",
                    "measure": "шт.",
                }
                for line in lines
            ],
        }
        # При одной торговой точке Точка подставляет её сама; при нескольких — поле обязательно.
        if self.merchant_id:
            data["merchantId"] = self.merchant_id
        # Поле необязательное (swagger): не задано в .env — не передаём.
        if self.tax_system_code:
            data["taxSystemCode"] = self.tax_system_code
        response = self.client.post("payments_with_receipt", json={"Data": data})
        if response.is_error:
            logger.error("Точка: ошибка создания платежа %s: %s", response.status_code, response.text)
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
