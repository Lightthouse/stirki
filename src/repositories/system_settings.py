from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.system_settings import SystemSettings

# Значения на случай, если строка в system_settings отсутствует (совпадают с дефолтами схемы).
_DEFAULTS = dict(
    free_tariff_is_available=True,
    free_bag_slots=1,
    free_piece_slots=0,
    paid_bag_slots=5,
    paid_piece_slots=1,
    order_accept_from_hour=9,
    order_accept_to_hour=22,
    free_orders_per_address_per_day=1,
    ad_count=1,
    ad_duration_sec=1,
)


async def get_system_settings(session: AsyncSession) -> SystemSettings:
    result = await session.execute(select(SystemSettings).limit(1))
    return result.scalar_one_or_none() or SystemSettings(id=1, **_DEFAULTS)
