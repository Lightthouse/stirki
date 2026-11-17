import re
import secrets

# Отладочные номера: код для них всегда возвращается в ответе API и показывается на странице входа,
# SMS не отправляется, даже когда вход по SMS включён. Вход под ними ничего не открывает, кроме
# собственных заказов тестового клиента.
DEBUG_PHONES = frozenset({"79999999999", "78888888888"})


def generate_verification_code() -> str:
    """Generate a 4-digit verification code."""
    return f"{secrets.randbelow(10000):04d}"


def phone_digits(phone: str) -> str:
    """Номер в виде 7XXXXXXXXXX: только цифры, ведущая 8 заменена на 7 (как на странице входа)."""
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("8"):
        digits = "7" + digits[1:]
    return digits


def is_debug_phone(phone: str) -> bool:
    return phone_digits(phone) in DEBUG_PHONES
