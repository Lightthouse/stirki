import logging
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.enums import Handover, OrderStatusName, PaymentStatus
from src.models.client import Client
from src.models.order import Order, OrderStatus, OrderStatusHistory

logger = logging.getLogger(__name__)


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_status_by_slug(self, slug: str) -> OrderStatus:
        result = await self.session.execute(
            select(OrderStatus).where(OrderStatus.slug == slug)
        )
        status = result.scalar_one_or_none()
        if not status:
            raise ValueError(f"Order status '{slug}' not found")
        return status

    async def create(
        self,
        client: Client,
        washing_type: str,
        bags_number: int,
        pieces_number: int,
        services: dict[str, bool],
        total_price_rub: int,
        status_name: str,
        comment: str | None = None,
        is_free: bool = False,
        next_day_delivery: bool = False,
        handover: str = Handover.DOOR,
        payment_status: str = PaymentStatus.PENDING,
    ) -> Order:
        status = await self.get_status_by_slug(status_name)

        order = Order(
            client_id=client.id,
            status_id=status.id,
            is_free=is_free,
            next_day_delivery=next_day_delivery,
            handover=handover,
            total_price_rub=total_price_rub,
            payment_status=payment_status,
            comment=comment,
            street=client.street,
            house=client.house,
            entrance=client.entrance,
            floor=client.floor,
            apartment=client.apartment,
            washing_type=washing_type,
            bags_number=bags_number,
            pieces_number=pieces_number,
            **services,
        )
        client.total_orders += 1
        self.session.add(order)
        await self.session.commit()
        await self.session.refresh(order)

        order.client = client
        order.status = status

        history = OrderStatusHistory(
            order_id=order.id,
            status_id=status.id,
            changed_by="system",
        )
        self.session.add(history)
        await self.session.commit()

        return order


    async def get_by_id(self, order_id: int) -> Order | None:
        result = await self.session.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.client), selectinload(Order.status))
        )
        return result.scalar_one_or_none()

    async def has_active_order(self, client_id: int) -> bool:
        result = await self.session.execute(
            select(Order)
            .join(OrderStatus, Order.status_id == OrderStatus.id)
            .where(
                Order.client_id == client_id,
                # Неоплаченный заказ не блокирует новый: брошенная оплата не должна
                # запирать клиента (такие заказы сами отменяются по EXPIRED от Точки).
                OrderStatus.slug.not_in([
                    OrderStatusName.DELIVERED,
                    OrderStatusName.CANCELED,
                    OrderStatusName.WAITING_PAYMENT,
                ]),
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def get_by_client_id(self, client_id: int) -> list[Order]:
        result = await self.session.execute(
            select(Order)
            .where(Order.client_id == client_id)
            # Платный заказ, для которого Точка так и не выдала ссылку на оплату (ошибка при
            # создании платежа), для клиента не состоялся: скрываем его из истории, чтобы он не
            # выглядел как «отменённый нами». В БД и админке такие заказы остаются для разбора.
            .where(~(
                Order.is_free.is_(False)
                & Order.operation_id.is_(None)
                & Order.status.has(slug=OrderStatusName.CANCELED)
            ))
            .options(selectinload(Order.status))
            .order_by(Order.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        order: Order,
        status_name: str,
        payment_status: str | None = None,
        changed_by: str = "system",
    ) -> Order:
        new_status = await self.get_status_by_slug(status_name)
        order.status_id = new_status.id
        if payment_status:
            order.payment_status = payment_status

        history = OrderStatusHistory(
            order_id=order.id,
            status_id=new_status.id,
            changed_by=changed_by,
        )
        self.session.add(history)
        await self.session.commit()
        await self.session.refresh(order, attribute_names=["status_id", "payment_status", "updated_at", "status"])

        return order

    async def update_payment(
        self,
        order: Order,
        operation_id: str,
        payment_link: str | None = None,
        payment_token: str | None = None,
        payment_link_id: str | None = None,
    ) -> Order:
        order.operation_id = operation_id
        if payment_link:
            order.payment_link = payment_link
        if payment_token:
            order.payment_token = payment_token
        if payment_link_id:
            order.payment_link_id = payment_link_id
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def get_by_payment_token(self, payment_token: str) -> Order | None:
        result = await self.session.execute(
            select(Order)
            .where(Order.payment_token == payment_token)
            .options(selectinload(Order.client), selectinload(Order.status))
        )
        return result.scalar_one_or_none()

    async def count_free_orders_for_address_since(
        self, street: str, house: str, apartment: int, since: datetime
    ) -> int:
        """Сколько неотменённых бесплатных заказов было на адрес начиная с `since`."""
        result = await self.session.execute(
            select(func.count(Order.id))
            .join(OrderStatus, Order.status_id == OrderStatus.id)
            .where(
                Order.is_free == True,  # noqa: E712
                Order.street == street,
                Order.house == house,
                Order.apartment == apartment,
                Order.created_at >= since,
                OrderStatus.slug != OrderStatusName.CANCELED,
            )
        )
        return result.scalar_one()

    async def get_waiting_payment(self) -> list[Order]:
        result = await self.session.execute(
            select(Order)
            .join(OrderStatus, Order.status_id == OrderStatus.id)
            .where(
                OrderStatus.slug == OrderStatusName.WAITING_PAYMENT,
                Order.operation_id.is_not(None),
            )
            .options(selectinload(Order.client), selectinload(Order.status))
        )
        return list(result.scalars().all())

    async def resolve_payment(
        self,
        order: Order,
        status_name: str,
        payment_status: str,
        changed_by: str,
    ) -> bool:
        """Атомарно перевести заказ из «оплата pending» в итоговое состояние.

        Возвращает True только тому вызову, который реально сменил статус —
        это защищает от двойных уведомлений, когда оплату одновременно проверяют
        фоновая задача и клиент.
        """
        new_status = await self.get_status_by_slug(status_name)
        result = await self.session.execute(
            update(Order)
            .where(Order.id == order.id, Order.payment_status == PaymentStatus.PENDING)
            .values(status_id=new_status.id, payment_status=payment_status, updated_at=func.now())
            .returning(Order.id)
        )
        changed = result.scalar_one_or_none() is not None
        if changed:
            self.session.add(OrderStatusHistory(
                order_id=order.id, status_id=new_status.id, changed_by=changed_by,
            ))
        await self.session.commit()
        await self.session.refresh(
            order, attribute_names=["status_id", "payment_status", "updated_at", "status"]
        )
        return changed
