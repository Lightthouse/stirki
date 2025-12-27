from src.enums import ServiceSlug, ServiceCyrillicSlugMap
from datetime import datetime
from typing import Optional

class Pricing:
    """
    Простая реализация прайсинга на основе констант.
    Потом её легко будет заменить на загрузку цен из БД.
    """

    WASHING_PRICE: int = 990

    SERVICE_PRICES: dict[ServiceSlug, int] = {
        ServiceSlug.IRONING: 990,
        ServiceSlug.CONDITIONER: 200,
        ServiceSlug.VACUUM_PACK: 400,
        ServiceSlug.EXACT_TIME: 300,
        ServiceSlug.UV: 300,
        ServiceSlug.WASH_BAG: 300,
    }

    @classmethod
    def get_price(cls, slug: ServiceSlug) -> int:
        return cls.SERVICE_PRICES[slug]

    @classmethod
    def services_price_message(cls, services: dict[ServiceSlug, bool]) -> str:
        """
        Создаём текст с ценами за дополнительные услуги
        :param services:
        :return:
        """
        slug_cyrillic_map = {v:k for k,v in ServiceCyrillicSlugMap.items()}
        message = ''.join([
            f' — {slug_cyrillic_map[name]}: {cls.SERVICE_PRICES[name]}\n' for name, picked in services.items() if picked
        ])

        return message

    @classmethod
    def total_price_message(cls, services: dict[ServiceSlug, bool]) -> str:
        """
        Создаём текст с итоговой ценой за все услуги
        :param services:
        :return:
        """

        services_message = cls.services_price_message(services)
        total_price = cls.calculate_order_price(services)

        message = f'Стирка: {cls.WASHING_PRICE}\n'
        if services_message:
            message += f'Доп. услуги:\n{services_message}'

        message += f'Итого: {total_price}\n'

        return message

    @classmethod
    def calculate_order_price(cls, services: dict[ServiceSlug, bool]) -> int:
        """
        Считает итоговую стоимость заказа по набору флагов.
        Вся формула сосредоточена здесь.
        """
        total = cls.WASHING_PRICE
        total += sum( cls.SERVICE_PRICES[name] for name, picked in services.items() if picked)

        return total

