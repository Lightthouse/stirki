# src/repositories.py
from src.models.models import Client, Order, OrderStatus, Street, OrderStatusHistory
from tortoise.functions import Coalesce
from datetime import datetime
from typing import Optional

class Repository:
    # ── Клиенты ─────────────────────────────────────
    @staticmethod
    async def get_or_create_client(
        telegram_id: int,
        phone: str,
        name: Optional[str] = None,
        street_name: Optional[str] = None,
        house: Optional[str] = None,
        entrance: Optional[str] = None,
        floor: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> Client:
        street = None
        if street_name:
            street = await Street.get_or_create(name=street_name.strip().title())[0]

        client, created = await Client.get_or_create(
            telegram_id=telegram_id,
            defaults={
                "phone": phone,
                "name": name,
                "street": street,
                "house": house or "",
                "entrance": entrance,
                "floor": floor,
                "comment": comment,
            },
        )
        if not created and (street or house):
            # Обновляем адрес, если клиент уже был
            update_fields = []
            if street and client.street != street:
                client.street = street
                update_fields.append("street")
            if house and client.house != house:
                client.house = house
                update_fields.append("house")
            if entrance and client.entrance != entrance:
                client.entrance = entrance
                update_fields.append("entrance")
            if floor and client.floor != floor:
                client.floor = floor
                update_fields.append("floor")
            if comment and client.comment != comment:
                client.comment = comment
                update_fields.append("comment")
            if update_fields:
                await client.save(update_fields=update_fields)

        if created:
            client.total_orders = 0
            await client.save()
        return client

    # ── Статусы ─────────────────────────────────────
    @staticmethod
    async def get_status_by_name(name: str) -> OrderStatus:
        return await OrderStatus.get(name=name)

    # ── Заказы ──────────────────────────────────────
    @staticmethod
    async def create_order(
        client: Client,
        street_name: str,
        house: str,
        services: dict,
        comment: Optional[str] = None,
        delivery_exact_time: Optional[datetime] = None,
    ) -> Order:
        street = await Street.get(name=street_name.strip().title())

        # Базовая цена — всегда стирка 3 кг
        total = 990

        need_ironing = services.get("ironing", False)
        need_conditioner = services.get("conditioner", False)
        need_vacuum_pack = services.get("vacuum_pack", False)
        need_uv = services.get("uv", False)
        need_wash_bag = services.get("wash_bag", False)

        if need_ironing:
            total += 990
        if need_conditioner:
            total += 200
        if need_vacuum_pack:
            total += 400
        if need_uv:
            total += 300
        if need_wash_bag:
            total += 300
        if delivery_exact_time:
            total += 300

        status_new = await OrderStatus.get(name="new")

        order = await Order.create(
            client=client,
            status=status_new,
            street=street,
            house=house,
            entrance=client.entrance,
            floor=client.floor,
            comment=comment or client.comment,
            total_price_rub=total,
            need_ironing=need_ironing,
            need_conditioner=need_conditioner,
            need_vacuum_pack=need_vacuum_pack,
            need_uv=need_uv,
            need_wash_bag=need_wash_bag,
            delivery_exact_time=delivery_exact_time,
        )

        # История статуса
        await OrderStatusHistory.create(
            order=order, status=status_new, changed_by="client"
        )

        # Увеличиваем счётчик заказов клиента
        client.total_orders += 1
        await client.save(update_fields=["total_orders"])

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
        order.updated_at = datetime.utcnow()
        await order.save(update_fields=["status", "updated_at"])

        await OrderStatusHistory.create(
            order=order, status=new_status, changed_by=changed_by
        )
        return order

    @staticmethod
    async def get_order_by_id(order_id: int) -> Optional[Order]:
        return await Order.get_or_none(id=order_id).prefetch_related("client", "status", "street")

# Удобный экземпляр
repo = Repository()
