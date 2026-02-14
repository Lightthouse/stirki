import logging

from yookassa import Configuration, Payment

from src.settings import YooKassaSettings

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self):
        settings = YooKassaSettings()
        Configuration.account_id = settings.YOOKASSA_SHOP_ID
        Configuration.secret_key = settings.YOOKASSA_SECRET_KEY
        self.return_url = settings.YOOKASSA_RETURN_URL

    def create_payment(
        self,
        amount: int,
        order_id: int,
        description: str = "Оплата заказа на стирку",
    ) -> dict:
        """Create a YooKassa payment with SBP method."""
        payment = Payment.create(
            {
                "amount": {"value": str(amount), "currency": "RUB"},
                "confirmation": {
                    "type": "redirect",
                    "return_url": f"{self.return_url}/orders/{order_id}",
                },
                "capture": True,
                "description": description,
                "metadata": {"order_id": str(order_id)},
            }
        )

        return {
            "payment_id": payment.id,
            "confirmation_url": payment.confirmation.confirmation_url
            if payment.confirmation
            else None,
            "status": payment.status,
        }

    @staticmethod
    def get_payment(payment_id: str) -> dict:
        """Get payment status from YooKassa."""
        payment = Payment.find_one(payment_id)
        return {
            "payment_id": payment.id,
            "status": payment.status,
            "metadata": payment.metadata,
        }
