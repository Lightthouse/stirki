from src.enums import ServiceSlug, ServiceCyrillicSlugMap
from datetime import datetime
from typing import Optional

class Pricing:
    """
    Работа с ценами через константы.
    Возможен дальнейший перенос в БД.
    """

    WASHING_PRICE: int = 890

    SERVICE_PRICES: dict[ServiceSlug, int] = {
        ServiceSlug.IRONING: 990,
        ServiceSlug.CONDITIONER: 50,
        ServiceSlug.VACUUM_PACK: 150,
        ServiceSlug.BLEACH: 80,
        ServiceSlug.STAIN_REMOVER: 80,
        ServiceSlug.COLOR_CATCHER_SHEETS: 30,
        ServiceSlug.WASH_BAG: 30,
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
    def total_price_message(cls, bags_number: int, services: dict[ServiceSlug, bool]) -> str:
        """
        Создаём текст с итоговой ценой за все услуги
        :param bags_number: количество пакетов с одеждой
        :param services: выбранные клиентом сервисы
        :return:
        """

        services_message = cls.services_price_message(services)
        total_price = cls.calculate_order_price(bags_number, services)

        message = f'Стирка: {cls.WASHING_PRICE}\n'
        if services_message:
            message += f'Доп. услуги:\n{services_message}'

        message += (
            f'Количество пакетов с одеждой: {bags_number}\n'
            f'Цена с услугами за один пакет: {total_price // 2}\n'
            f'Итого: {total_price}\n'
        )

        return message

    @classmethod
    def calculate_order_price(cls, bags_number: int, services: dict[ServiceSlug, bool]) -> int:
        """
        Считает итоговую стоимость заказа по набору флагов.
        Вся формула сосредоточена здесь.
        """
        total = cls.WASHING_PRICE
        total += sum( cls.SERVICE_PRICES[name] for name, picked in services.items() if picked)

        print(services)
        print([cls.SERVICE_PRICES[name] for name, picked in services.items() if picked])
        return total * bags_number

