import re

from pydantic import BaseModel, field_validator

from src.services.auth import phone_digits

# Простая проверка формата: точную проверку адреса делает Точка при отправке чека.
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RequestCodeIn(BaseModel):
    phone: str
    # Галочка «Принимаю оферту и политику конфиденциальности». Нужна только при регистрации:
    # без неё новому номеру код не отправляем, зарегистрированный клиент её уже принял.
    offer_accepted: bool = False

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # 11 цифр с 7. Что номер мобильный (или отладочный из настроек), проверяет роутер.
        # Сам номер храним как прислал фронтенд (+7 999 123-45-67), меняем только проверку.
        if not re.fullmatch(r"7\d{10}", phone_digits(v)):
            raise ValueError("Введите номер мобильного телефона полностью")
        return v.strip()


class RequestCodeOut(BaseModel):
    message: str
    # True — номер не зарегистрирован, код не отправлен: нужно показать шаг регистрации
    # (email, оферта, рассылка) и запросить код снова с offer_accepted.
    registration_required: bool = False
    # код на странице: вход по SMS выключен в админке или номер отладочный
    code: str | None = None


class VerifyCodeIn(BaseModel):
    phone: str
    code: str
    # Поля ниже — только при регистрации; при входе зарегистрированного клиента игнорируются.
    offer_accepted: bool = False
    # необязательная галочка «Согласен на рекламные и информационные СМС»
    sms_marketing_consent: bool = False
    # email для кассовых чеков (Точка отправляет чек об оплате на почту)
    email: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is None or not v.strip():
            return None
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
