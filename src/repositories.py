import logging
import asyncio
from datetime import datetime
from typing import Optional
from icecream import ic

from src.models import Client, Order, OrderStatus, Street, OrderStatusHistory
from src.enums import ServiceSlug, OrderStatusName, PaymentStatus, KaitenColumns, KaitenTagsNames
from src.services.pricing import Pricing
from src.services.kaiten_kanban import Kaiten

logger = logging.getLogger(__name__)


class Repository:

    @staticmethod
    async def resolve_client_street(client: Client) -> Optional[Street]:
        """
        Гарантированно получить объект Street для клиента.

        Поведение:
        - пытаемся сделать client.fetch_related("street") и вернуть client.street;
        - если всё ещё None, кидаем ошибку;
        """
        await client.fetch_related("street")

        if client.street is None:
            raise ValueError("У клиента не указан адрес")

        return client.street

    @staticmethod
    async def resolve_street_by_name(street_name: str) -> Street:
        street = await Street.get_or_none(name=street_name)
        if not street:
            raise ValueError(f"Unknown street: {street_name}")
        return street

    # ── Клиенты ─────────────────────────────────────
    @staticmethod
    async def get_client_by_telegram_id(telegram_id: int) -> Client | None:
        return await Client.get_or_none(telegram_id=telegram_id)

    @staticmethod
    async def fill_client(
            telegram_id: int,
            phone: str,
            name: str,
            street: Street,
            house: str,
            entrance: str,
            floor: str,
            apartment: int,
            comment: str | None,
    ) -> Client:
        return await Client.create(
            telegram_id=telegram_id,
            phone=phone,
            name=name,
            street=street,
            house=house,
            entrance=entrance,
            floor=floor,
            apartment=apartment,
            comment=comment,
        )

    @staticmethod
    async def create_client(
            telegram_id: int,
            phone: str,
            name: str,
            street: str,
            apartment: int,
            house: str,

            entrance: str = None,
            floor: str = None,
            comment: str = None,
    ) -> Client:

        street = await Repository.resolve_street_by_name(street)


        return await Client.create(
            telegram_id=telegram_id,
            phone=phone,
            name=name,
            street=street,
            apartment=apartment,
            house=house,

            entrance=entrance,
            floor=floor,
            comment=comment,
        )

    @staticmethod
    async def update_client(
            telegram_id: int,
            phone: str | None,
            name: str | None,
            street: str | None,
            house: str | None,
            apartment: int,
            entrance: str | None,
            floor: str | None,
            comment: str | None,
    ) -> Client:

        client = await Client.get(telegram_id=telegram_id)

        client.phone = phone
        client.name = name

        client.street = street
        client.house = house
        client.apartment = apartment
        client.entrance = entrance
        client.floor = floor
        client.comment = comment
        await client.save(
            update_fields=["phone", "name", "street", "apartment", "house", "entrance", "floor", "comment"]
        )
        return client

    # ── Статусы ─────────────────────────────────────
    @staticmethod
    async def get_status_by_name(name: str) -> OrderStatus:
        return await OrderStatus.get(name=name)

    # ── Заказы ──────────────────────────────────────
    @staticmethod
    async def create_order(
            client: Client,
            telegram_chat_id: int,
            telegram_message_id: int,
            services: dict[ServiceSlug, bool],
            comment: str = None,
    ) -> Order:

        street = await Repository.resolve_client_street(client)

        # Считаем цену заказа
        total = Pricing.calculate_order_price(services)

        # Берём самый первый статус
        status_new = await OrderStatus.get(name=OrderStatusName.WAITING_FOR_CAPTURE)

        # Создаём заказ
        order = await Order.create(
            client=client,
            status=status_new,
            total_price_rub=total,
            payment_status=PaymentStatus.WAITING_FOR_CAPTURE,
            comment=comment,

            telegram_chat_id=telegram_chat_id,
            telegram_message_id=telegram_message_id,

            street=street,
            house=client.house,
            entrance=client.entrance,
            floor=client.floor,
            apartment=client.apartment,

            **services
        )

        # Создаём kaiten карточку
        with Kaiten() as k:
            await k.add_card_to_order(order)

        # История статуса
        await OrderStatusHistory.create(
            order=order,
            status=status_new,
            changed_by="system",
        )

        return order

    @staticmethod
    async def attach_telegram_message(order_id: int, chat_id: int, message_id: int) -> Optional[Order]:
        order = await Order.get(id=order_id)
        order.telegram_chat_id = chat_id
        order.telegram_message_id = message_id
        await order.save(update_fields=["telegram_chat_id", "telegram_message_id"])
        return order

    @staticmethod
    async def update_order_status(
            order_id: int,
            status: OrderStatusName,
            payment_status: PaymentStatus,
            changed_by: str = "system",
    ) -> Order:
        order = await Order.get(id=order_id)

        order_status_obj = await OrderStatus.get(name=status)

        # Самый понятный и надёжный способ:
        order.status_id = order_status_obj.id
        order.payment_status = payment_status

        await order.save(update_fields=["status_id", "payment_status"])

        # история статусов
        await OrderStatusHistory.create(
            order=order,
            status=order_status_obj,  # здесь объект — нормально
            changed_by=changed_by
        )

        # Kaiten-логика...
        with Kaiten() as k:
            card_status = (
                KaitenColumns.NEW
                if status == OrderStatusName.NEW
                else KaitenColumns.CANCELED
            )
            if order.kaiten_card_id:
                k.change_card_status(order.kaiten_card_id, card_status)
                logger.info(f"Card {order.kaiten_card_id} → {status}")

        return order

    @staticmethod
    async def get_order_by_id(order_id: int) -> Optional[Order]:
        return await (
            Order.filter(id=order_id)
            .prefetch_related("client", "status", "street")
            .first()
        )

    @staticmethod
    async def reset_db() -> str:
        await Order.all().delete()
        await Client.all().delete()
        await OrderStatusHistory.all().delete()

        return 'Всё уничтожено!'


# Удобный экземпляр
repo = Repository()
