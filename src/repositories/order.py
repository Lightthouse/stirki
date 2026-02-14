import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.enums import OrderStatusName, PaymentStatus, KaitenColumns
from src.models.client import Client
from src.models.order import Order, OrderStatus, OrderStatusHistory
from src.services.kaiten_kanban import Kaiten

logger = logging.getLogger(__name__)


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_status_by_name(self, name: str) -> OrderStatus:
        result = await self.session.execute(
            select(OrderStatus).where(OrderStatus.name == name)
        )
        status = result.scalar_one_or_none()
        if not status:
            raise ValueError(f"Order status '{name}' not found")
        return status

    async def create(
        self,
        client: Client,
        bags_number: int,
        services: dict[str, bool],
        total_price_rub: int,
        comment: str | None = None,
    ) -> Order:
        status = await self.get_status_by_name(OrderStatusName.WAITING_FOR_CAPTURE)

        order = Order(
            client_id=client.id,
            status_id=status.id,
            total_price_rub=total_price_rub,
            payment_status=PaymentStatus.PENDING,
            comment=comment,
            street=client.street,
            house=client.house,
            entrance=client.entrance,
            floor=client.floor,
            apartment=client.apartment,
            bags_number=bags_number,
            **services,
        )
        self.session.add(order)
        await self.session.commit()
        await self.session.refresh(order)

        # Подгружаем клиента для Kaiten
        order.client = client
        order.status = status

        # Kaiten карточка
        try:
            with Kaiten() as k:
                await k.add_card_to_order(order)
                await self.session.refresh(order)
        except Exception:
            logger.exception("Failed to create Kaiten card for order %s", order.id)

        # История статуса
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

    async def get_by_client_id(self, client_id: int) -> list[Order]:
        result = await self.session.execute(
            select(Order)
            .where(Order.client_id == client_id)
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
        new_status = await self.get_status_by_name(status_name)
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
        await self.session.refresh(order)

        # Kaiten
        try:
            if order.kaiten_card_id:
                column = getattr(KaitenColumns, status_name.upper(), None)
                if column:
                    with Kaiten() as k:
                        k.change_card_status(order.kaiten_card_id, column)
                        logger.info("Card %s -> %s", order.kaiten_card_id, status_name)
        except Exception:
            logger.exception("Failed to update Kaiten card for order %s", order.id)

        return order

    async def update_payment(
        self,
        order: Order,
        yookassa_payment_id: str,
        yookassa_confirmation_url: str | None = None,
    ) -> Order:
        order.yookassa_payment_id = yookassa_payment_id
        if yookassa_confirmation_url:
            order.yookassa_confirmation_url = yookassa_confirmation_url
        await self.session.commit()
        await self.session.refresh(order)
        return order
