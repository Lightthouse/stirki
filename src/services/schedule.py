from datetime import datetime, timedelta, timezone

from src.models.system_settings import SystemSettings

# Москва живёт в UTC+3 без перехода на летнее время; фиксированный offset
# избавляет от зависимости от tzdata в slim-образе.
MSK = timezone(timedelta(hours=3), "MSK")


def now_msk() -> datetime:
    return datetime.now(MSK)


def start_of_today_msk() -> datetime:
    return now_msk().replace(hour=0, minute=0, second=0, microsecond=0)


def time_to_minutes(value: str) -> int:
    """«7:30» / «07:30» → минуты от начала суток; «24:00» → 1440 (конец суток)."""
    hours, minutes = value.strip().split(":")
    return int(hours) * 60 + int(minutes)


def format_time(value: str) -> str:
    """«07:30» → «7:30» — так часы приёма пишутся клиентам."""
    minutes = time_to_minutes(value)
    return f"{minutes // 60}:{minutes % 60:02d}"


def is_accepting_orders(settings: SystemSettings, now: datetime | None = None) -> bool:
    now = now or now_msk()
    current = now.hour * 60 + now.minute
    return time_to_minutes(settings.order_accept_from) <= current < time_to_minutes(settings.order_accept_to)


def is_next_day_delivery(settings: SystemSettings, now: datetime | None = None) -> bool:
    """Заказ, оформленный в `now`, забирают сразу, а возвращают на следующий день."""
    now = now or now_msk()
    return now.hour >= settings.next_day_delivery_from_hour


def accept_hours_text(settings: SystemSettings) -> str:
    return f"с {format_time(settings.order_accept_from)} до {format_time(settings.order_accept_to)}"
