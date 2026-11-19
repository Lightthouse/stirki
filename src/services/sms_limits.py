"""Лимиты SMS-кодов на один IP — защита бюджета SmsAero от перебора номеров.

Ограничение «раз в 58 с на номер» (src/api/routers/auth.py) не мешает скрипту перебирать разные номера —
каждый запрос стоит настоящую SMS. Поэтому отправки считаются ещё и по IP: за 10 минут, сутки и неделю.
Значения — в админке («Системные настройки»), меняются без деплоя. Общий потолок SMS — в кабинете SmsAero.
Отправки хранятся в БД (sms_sends), а не в памяти: иначе недельный счётчик обнулялся бы при каждом деплое.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.analytics import SmsSend
from src.models.system_settings import SystemSettings

KEEP_FOR = timedelta(days=30)


def _windows(settings: SystemSettings) -> list[tuple[timedelta, int]]:
    return [
        (timedelta(minutes=10), settings.sms_ip_limit_10min),
        (timedelta(days=1), settings.sms_ip_limit_day),
        (timedelta(days=7), settings.sms_ip_limit_week),
    ]


async def seconds_until_allowed(session: AsyncSession, ip: str, settings: SystemSettings) -> int:
    """0 — с этого IP можно отправить SMS; иначе — через сколько секунд освободится место во всех окнах."""
    windows = _windows(settings)
    now = datetime.now(timezone.utc)
    since = now - max(w for w, _ in windows)
    result = await session.execute(
        select(SmsSend.sent_at).where(SmsSend.ip == ip, SmsSend.sent_at > since).order_by(SmsSend.sent_at.desc())
    )
    sent = list(result.scalars())  # новые первыми

    wait = 0.0
    for window, limit in windows:
        in_window = [t for t in sent if t > now - window]
        if len(in_window) >= limit:
            # Место освободится, когда из окна выйдет самая старая из `limit` последних отправок.
            oldest_blocking = in_window[limit - 1] if limit > 0 else now
            wait = max(wait, (oldest_blocking + window - now).total_seconds())
    return int(wait) + 1 if wait > 0 else 0


async def record_send(session: AsyncSession, ip: str, phone: str) -> None:
    session.add(SmsSend(ip=ip, phone=phone))
    # Старые записи не нужны ни для лимитов, ни для разбора — таблица остаётся маленькой.
    await session.execute(delete(SmsSend).where(SmsSend.sent_at < datetime.now(timezone.utc) - KEEP_FOR))
    await session.commit()


def wait_text(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds} сек"
    if seconds < 3600:
        return f"{(seconds + 59) // 60} мин"
    hours = (seconds + 3599) // 3600
    if hours < 24:
        return f"{hours} ч"
    return f"{(hours + 23) // 24} дн"
