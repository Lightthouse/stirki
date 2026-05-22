from datetime import datetime

from pydantic import BaseModel


class CreateOrderIn(BaseModel):
    street: str
    house: str
    apartment: int
    entrance: int = 1
    floor: int = 1
    bags_number: int = 0
    pieces_number: int = 0
    services: list[str] = []
    comment: str | None = None
    is_free: bool = False


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
    pieces_number: int
    services: list[str]
    total_price_rub: int
    payment_status: str
    is_free: bool
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
    pieces_number: int
    created_at: datetime
