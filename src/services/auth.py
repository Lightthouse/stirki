import re
import secrets

from src.models.system_settings import SystemSettings


def generate_verification_code() -> str:
    """Generate a 4-digit verification code."""
    return f"{secrets.randbelow(10000):04d}"


def phone_digits(phone: str) -> str:
    """Номер в виде 7XXXXXXXXXX: только цифры, ведущая 8 заменена на 7 (как на странице входа)."""
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("8"):
        digits = "7" + digits[1:]
    return digits


def parse_phone_list(text: str) -> list[str]:
    """Список номеров из настройки: через запятую, точку с запятой или с новой строки → ['7XXXXXXXXXX', …]."""
    return [phone_digits(p) for p in re.split(r"[,;\n]", text) if p.strip()]


def is_mobile_phone(phone: str) -> bool:
    """Российский мобильный (79XXXXXXXXX): другие номера SmsAero не примет, а каждая попытка — деньги."""
    return re.fullmatch(r"79\d{9}", phone_digits(phone)) is not None


def is_debug_phone(phone: str, settings: SystemSettings) -> bool:
    """Отладочный номер: код показывается на странице входа, SMS не шлётся, даже когда вход по SMS включён.
    Номера и флаг — в админке («Системные настройки»); при выключенном флаге список не действует."""
    return settings.debug_phones_enabled and phone_digits(phone) in parse_phone_list(settings.debug_phones)
