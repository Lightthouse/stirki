"""Сверка статуса оплаты с Точка Банком.

Вебхуков нет, поэтому статус подтягивается тремя путями:
- клиент вернулся по редиректу (POST /api/payments/verify/{id});
- клиент открыл заказ или список заказов;
- фоновая задача раз в минуту проверяет все заказы «Ожидает оплаты»
  (на случай, если клиент оплатил в приложении банка и не вернулся на сайт).

Клиент может отменить неоплаченный заказ, но аннулировать ссылку в Точке нельзя — она живёт
PAYMENT_LINK_TTL_MINUTES. Поэтому фоновая задача ещё следит за такими заказами: если оплата
всё же пришла, заказ помечается оплаченным (статус остаётся «Отменён») и операторам уходит письмо.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session
from src.enums import OrderStatusName, PaymentStatus
from src.models.order import Order
from src.repositories.order import OrderRepository
from src.services.notifications import notify_new_order, notify_paid_after_cancel
from src.services.payment import PAYMENT_LINK_TTL_MINUTES, PaymentService

logger = logging.getLogger(__name__)

SYNC_INTERVAL_SECONDS = 60
# Сколько следить за отменённым клиентом заказом: ссылка живёт час, плюс запас на задержку статуса в Точке.
CANCELED_WATCH = timedelta(minutes=PAYMENT_LINK_TTL_MINUTES + 30)


async def _tochka_status(order: Order) -> str:
    """Статус операции в Точке (APPROVED, REJECTED, EXPIRED, CREATED…); при ошибке — ''."""
    try:
        info = await asyncio.to_thread(PaymentService().get_payment, order.operation_id)
    except Exception:
        logger.exception("Не удалось получить статус оплаты заказа %s", order.id)
        return ""
    operations = info.get("Data", {}).get("Operation", [])
    return operations[0].get("status", "").upper() if operations else ""


async def sync_order_payment(session: AsyncSession, order: Order) -> str:
    """Возвращает 'approved' | 'rejected' | 'pending'. Ошибки Точки → 'pending'."""
    if order.payment_status == PaymentStatus.SUCCEEDED:
        return "approved"
    if order.payment_status == PaymentStatus.CANCELED:
        return "rejected"
    if not order.operation_id:
        return "pending"

    tochka_status = await _tochka_status(order)
    repo = OrderRepository(session)

    if tochka_status == "APPROVED":
        changed = await repo.resolve_payment(
            order, OrderStatusName.COURIER_PICKUP, PaymentStatus.SUCCEEDED, changed_by="tochka",
        )
        if changed:
            await notify_new_order(session, order, order.client)
        return "approved"
    if tochka_status in ("REJECTED", "EXPIRED"):
        await repo.resolve_payment(
            order, OrderStatusName.CANCELED, PaymentStatus.CANCELED, changed_by="tochka",
        )
        return "rejected"
    return "pending"


async def check_paid_after_cancel(session: AsyncSession, order: Order) -> None:
    """Отменённый клиентом заказ всё-таки оплачен по старой ссылке — пометить и написать операторам."""
    if await _tochka_status(order) != "APPROVED":
        return
    if await OrderRepository(session).mark_paid_after_cancel(order):
        logger.warning("Заказ %s оплачен после отмены клиентом", order.id)
        await notify_paid_after_cancel(session, order, order.client)


async def payment_sync_loop() -> None:
    """Фоновая задача: периодически сверяет все неоплаченные заказы."""
    while True:
        await asyncio.sleep(SYNC_INTERVAL_SECONDS)
        try:
            async with async_session() as session:
                repo = OrderRepository(session)
                for order in await repo.get_waiting_payment():
                    await sync_order_payment(session, order)
                since = datetime.now(timezone.utc) - CANCELED_WATCH
                for order in await repo.get_canceled_by_client_since(since):
                    await check_paid_after_cancel(session, order)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Ошибка в фоновой сверке оплат")
