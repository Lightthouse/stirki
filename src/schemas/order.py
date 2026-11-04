from datetime import datetime

from pydantic import BaseModel, Field


class CreateOrderIn(BaseModel):
    street: str
    house: str
    apartment: int = Field(ge=1, le=1000)
    entrance: int = Field(default=1, ge=1, le=30)
    floor: int = Field(default=1, ge=1, le=50)
    bags_number: int = Field(default=0, ge=0)
    pieces_number: int = Field(default=0, ge=0)
    services: list[str] = []
    comment: str | None = Field(default=None, max_length=500)
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
    # Ссылка на оплату — только пока заказ ждёт оплаты, чтобы клиент мог вернуться к ней.
    payment_link: str | None = None
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
