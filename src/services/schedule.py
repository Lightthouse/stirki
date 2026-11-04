from datetime import datetime, timedelta, timezone

from src.models.system_settings import SystemSettings

# Москва живёт в UTC+3 без перехода на летнее время; фиксированный offset
# избавляет от зависимости от tzdata в slim-образе.
MSK = timezone(timedelta(hours=3), "MSK")


def now_msk() -> datetime:
    return datetime.now(MSK)


def start_of_today_msk() -> datetime:
    return now_msk().replace(hour=0, minute=0, second=0, microsecond=0)


def is_accepting_orders(settings: SystemSettings, now: datetime | None = None) -> bool:
    now = now or now_msk()
    return settings.order_accept_from_hour <= now.hour < settings.order_accept_to_hour


def accept_hours_text(settings: SystemSettings) -> str:
    return f"с {settings.order_accept_from_hour}:00 до {settings.order_accept_to_hour}:00"
