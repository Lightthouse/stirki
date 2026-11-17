import re

from pydantic import BaseModel, field_validator

from src.services.auth import phone_digits

# Простая проверка формата: точную проверку адреса делает Точка при отправке чека.
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RequestCodeIn(BaseModel):
    phone: str
    # галочка «Принимаю оферту и политику конфиденциальности» — без неё код не отправляем
    offer_accepted: bool = False

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # Российский мобильный: 11 цифр с 7 (SmsAero не примет неполный номер, а каждая попытка — деньги).
        # Сам номер храним как прислал фронтенд (+7 999 123-45-67), меняем только проверку.
        if not re.fullmatch(r"79\d{9}|78{10}", phone_digits(v)):
            raise ValueError("Введите номер мобильного телефона полностью")
        return v.strip()


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
