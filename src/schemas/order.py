from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class CreateOrderIn(BaseModel):
    street: str
    house: str
    apartment: int
    entrance: int = 1
    floor: int = 1
    washing_type: Literal['bag', 'piece'] = 'bag'
    bags_number: int = 1
    services: list[str] = []
    comment: str | None = None


class OrderOut(BaseModel):
    id: int
    status: str
    street: str
    house: str
    apartment: int
    entrance: int
    floor: int
    washing_type: str
    bags_number: int
    services: list[str]
    total_price_rub: int
    payment_status: str
    yookassa_confirmation_url: str | None
    comment: str | None
    created_at: datetime
    updated_at: datetime


class OrderListOut(BaseModel):
    id: int
    status: str
    total_price_rub: int
    payment_status: str
    washing_type: str
    bags_number: int
    created_at: datetime
