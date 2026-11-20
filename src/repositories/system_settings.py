from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.system_settings import DEFAULT_DEBUG_PHONES, SystemSettings

# Значения на случай, если строка в system_settings отсутствует (совпадают с дефолтами схемы).
_DEFAULTS = dict(
    free_tariff_is_available=True,
    sms_enabled=False,
    debug_phones_enabled=False,
    debug_phones=DEFAULT_DEBUG_PHONES,
    sms_ip_limit_10min=5,
    sms_ip_limit_day=15,
    sms_ip_limit_week=50,
    promo_enabled=True,
    promo_bag_price=990,
    promo_piece_price=190,
    promo_label="акция 7 дней",
    free_bag_slots=1,
    free_piece_slots=0,
    paid_bag_slots=5,
    paid_piece_slots=1,
    order_accept_from="07:30",
    order_accept_to="21:00",
    next_day_delivery_from_hour=19,
    free_orders_per_address_per_day=1,
    ad_count=2,
    ad_duration_sec=10,
    support_phone="",
    support_telegram="",
    support_email="",
    notify_emails="",
)


async def get_system_settings(session: AsyncSession) -> SystemSettings:
    result = await session.execute(select(SystemSettings).limit(1))
    return result.scalar_one_or_none() or SystemSettings(id=1, **_DEFAULTS)
