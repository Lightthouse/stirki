# src/repositories.py
import asyncio
from datetime import datetime
from typing import Optional



from src.models import Client, Order, OrderStatus, Street, OrderStatusHistory
from src.enums import ServiceSlug, OrderStatusName, PaymentStatus
from src.services.pricing import Pricing
from src.services.kanban import Kanban



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

    # ── Клиенты ─────────────────────────────────────
    @staticmethod
    async def get_client_by_telegram_id(telegram_id: int) -> Client | None:
        return await Client.get_or_none(telegram_id=telegram_id)

    @staticmethod
    async def create_client(
            telegram_id: int,
            phone: str,
            name: str | None,
            street: Street | None,
            house: str,
            entrance: str | None,
            floor: str | None,
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
            comment=comment,
        )

    @staticmethod
    async def update_client_address(
            client: Client,
            street: Street | None,
            house: str,
            entrance: str | None,
            floor: str | None,
            comment: str | None,
    ) -> Client:
        client.street = street
        client.house = house
        client.entrance = entrance
        client.floor = floor
        client.comment = comment
        await client.save(
            update_fields=["street", "house", "entrance", "floor", "comment"]
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
            comment: Optional[str],
            weight_kg: int = 3,
            need_ironing: bool = False,
            need_conditioner: bool = False,
            need_vacuum_pack: bool = False,
            need_uv: bool = False,
            need_wash_bag: bool = False,
            delivery_exact_time: Optional[datetime] = None,
    ) -> Order:

        street = await Repository.resolve_client_street(client)
        if street is None or not client.house:
            raise ValueError("У клиента не указан корректный адрес. Обновите адрес перед созданием заказа.")

        # Считаем цену заказа
        total = Pricing.calculate_order_total(
            need_ironing=need_ironing,
            need_conditioner=need_conditioner,
            need_vacuum_pack=need_vacuum_pack,
            need_uv=need_uv,
            need_wash_bag=need_wash_bag,
            delivery_exact_time=delivery_exact_time,
        )

        # Берём самый первый статус
        status_new = await OrderStatus.get(name=OrderStatusName.NEW)

        # Создаём заказ
        order = await Order.create(
            client=client,
            status=status_new,
            total_price_rub=total,
            payment_status=PaymentStatus.PENDING,
            comment=comment,

            street=street,
            house=client.house,
            entrance=client.entrance,
            floor=client.floor,

            weight_kg=weight_kg,
            need_ironing=need_ironing,
            need_conditioner=need_conditioner,
            need_vacuum_pack=need_vacuum_pack,
            need_uv=need_uv,
            need_wash_bag=need_wash_bag,
            delivery_exact_time=delivery_exact_time,
        )

        # Создаём trello карточку
        print('card creating')
        Kanban.configure()
        Kanban.enqueue_create_card(order)

        # История статуса
        await OrderStatusHistory.create(
            order=order,
            status=status_new,
            changed_by="system",
        )

        return order

    @staticmethod
    async def update_status(
            order: Order,
            new_status_name: str,
            changed_by: str = "system",
    ) -> Order:
        new_status = await OrderStatus.get(name=new_status_name)
        if order.status == new_status:
            return order

        order.status = new_status
        await order.save(update_fields=["status"])

        await OrderStatusHistory.create(
            order=order, status=new_status, changed_by=changed_by
        )
        return order

    @staticmethod
    async def get_order_by_id(order_id: int) -> Optional[Order]:
        return await (
            Order.filter(id=order_id)
            .prefetch_related("client", "status", "street")
            .first()
        )


# Удобный экземпляр
repo = Repository()
