import re

from pydantic import BaseModel, field_validator

# Простая проверка формата: точную проверку адреса делает Точка при отправке чека.
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RequestCodeIn(BaseModel):
    phone: str
    # галочка «Принимаю оферту и политику конфиденциальности» — без неё код не отправляем
    offer_accepted: bool = False


class VerifyCodeIn(BaseModel):
    phone: str
    code: str
    offer_accepted: bool = False
    # необязательная галочка «Согласен на рекламные и информационные СМС»
    sms_marketing_consent: bool = False
    # email для кассовых чеков (Точка отправляет чек об оплате на почту)
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if len(v) > 254 or not EMAIL_RE.match(v):
            raise ValueError("Некорректный email")
        return v


class AuthTokenOut(BaseModel):
    token: str
    is_new_client: bool
    client: "ClientOut | None" = None


class ClientOut(BaseModel):
    id: int
    phone: str
    name: str | None
    email: str | None
    street: str
    house: str
    apartment: int
    entrance: int
    floor: int

    model_config = {"from_attributes": True}


class UpdateClientIn(BaseModel):
    name: str | None = None
