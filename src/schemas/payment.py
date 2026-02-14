from pydantic import BaseModel


class PaymentOut(BaseModel):
    order_id: int
    total_price_rub: int
    confirmation_url: str | None


class YooKassaWebhookIn(BaseModel):
    type: str
    event: str
    object: dict
