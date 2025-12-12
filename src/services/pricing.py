from src.enums import ServiceSlug
from datetime import datetime
from typing import Optional

class Pricing:
    """
    Простая реализация прайсинга на основе констант.
    Потом её легко будет заменить на загрузку цен из БД.
    """

    SERVICE_PRICES: dict[ServiceSlug, int] = {
        ServiceSlug.BASE: 990,
        ServiceSlug.IRONING: 990,
        ServiceSlug.CONDITIONER: 200,
        ServiceSlug.VACUUM_PACK: 400,
        ServiceSlug.EXACT_TIME: 300,
        ServiceSlug.UV: 300,
        ServiceSlug.WASH_BAG: 300,
    }

    @classmethod
    def get_price(cls, slug: ServiceSlug) -> int:
        try:
            return cls.SERVICE_PRICES[slug]
        except KeyError as e:
            # Если забыли добавить slug в словарь — лучше упасть явно
            raise ValueError(f"Price for service {slug!r} is not configured") from e

    @classmethod
    def calculate_order_total(
        cls,
        *,
        need_ironing: bool = False,
        need_conditioner: bool = False,
        need_vacuum_pack: bool = False,
        need_uv: bool = False,
        need_wash_bag: bool = False,
        delivery_exact_time: Optional[datetime] = None,
        # на будущее тут можно добавить weight_kg, промокоды и т.п.
    ) -> int:
        """
        Считает итоговую стоимость заказа по набору флагов.
        Вся формула сосредоточена здесь.
        """
        total = cls.get_price(ServiceSlug.BASE)

        if need_ironing:
            total += cls.get_price(ServiceSlug.IRONING)
        if need_conditioner:
            total += cls.get_price(ServiceSlug.CONDITIONER)
        if need_vacuum_pack:
            total += cls.get_price(ServiceSlug.VACUUM_PACK)
        if need_uv:
            total += cls.get_price(ServiceSlug.UV)
        if need_wash_bag:
            total += cls.get_price(ServiceSlug.WASH_BAG)

        if delivery_exact_time is not None:
            total += cls.get_price(ServiceSlug.EXACT_TIME)

        return total