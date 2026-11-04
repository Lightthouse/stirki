"""Сверка статуса оплаты с Точка Банком.

Вебхуков нет, поэтому статус подтягивается тремя путями:
- клиент вернулся по редиректу (POST /api/payments/verify/{id});
- клиент открыл заказ или список заказов;
- фоновая задача раз в минуту проверяет все заказы «Ожидает оплаты»
  (на случай, если клиент оплатил в приложении банка и не вернулся на сайт).
"""

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session
from src.enums import OrderStatusName, PaymentStatus
from src.models.order import Order
from src.repositories.order import OrderRepository
from src.services.notifications import notify_new_order
from src.services.payment import PaymentService

logger = logging.getLogger(__name__)

SYNC_INTERVAL_SECONDS = 60


async def sync_order_payment(session: AsyncSession, order: Order) -> str:
    """Возвращает 'approved' | 'rejected' | 'pending'. Ошибки Точки → 'pending'."""
    if order.payment_status == PaymentStatus.SUCCEEDED:
        return "approved"
    if order.payment_status == PaymentStatus.CANCELED:
        return "rejected"
    if not order.operation_id:
        return "pending"

    try:
        info = await asyncio.to_thread(PaymentService().get_payment, order.operation_id)
    except Exception:
        logger.exception("Не удалось получить статус оплаты заказа %s", order.id)
        return "pending"

    operations = info.get("Data", {}).get("Operation", [])
    tochka_status = operations[0].get("status", "").upper() if operations else ""
    repo = OrderRepository(session)

    if tochka_status == "APPROVED":
        changed = await repo.resolve_payment(
            order, OrderStatusName.COURIER_PICKUP, PaymentStatus.SUCCEEDED, changed_by="tochka",
        )
        if changed:
            notify_new_order(order, order.client)
        return "approved"
    if tochka_status in ("REJECTED", "EXPIRED"):
        await repo.resolve_payment(
            order, OrderStatusName.CANCELED, PaymentStatus.CANCELED, changed_by="tochka",
        )
        return "rejected"
    return "pending"


async def payment_sync_loop() -> None:
    """Фоновая задача: периодически сверяет все неоплаченные заказы."""
    while True:
        await asyncio.sleep(SYNC_INTERVAL_SECONDS)
        try:
            async with async_session() as session:
                for order in await OrderRepository(session).get_waiting_payment():
                    await sync_order_payment(session, order)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Ошибка в фоновой сверке оплат")
