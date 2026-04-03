import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.enums import OrderStatusName, PaymentStatus
from src.services.order import OrderService
from src.settings import AppSettings

logger = logging.getLogger(__name__)

router = APIRouter()
app_settings = AppSettings()


@router.post("/webhook")
async def yookassa_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """Handle YooKassa payment notifications."""
    body = await request.json()

    payment_obj = body.get("object", {})
    payment_id = payment_obj.get("id")
    payment_status = payment_obj.get("status")
    metadata = payment_obj.get("metadata", {})
    order_id = metadata.get("order_id")

    if not order_id or not payment_id:
        logger.warning("Webhook missing order_id or payment_id: %s", body)
        return {"status": "ignored"}

    order_service = OrderService(session)
    order = await order_service.get_by_id(int(order_id))

    if not order:
        logger.warning("Order %s not found for webhook", order_id)
        return {"status": "ignored"}

    if order.yookassa_payment_id and order.yookassa_payment_id != payment_id:
        logger.warning(
            "Payment ID mismatch: order has %s, webhook has %s",
            order.yookassa_payment_id,
            payment_id,
        )
        return {"status": "ignored"}

    if payment_status == "succeeded":
        await order_service.update_status(
            order,
            status_name=OrderStatusName.NEW,
            payment_status=PaymentStatus.SUCCEEDED,
            changed_by="yookassa",
        )
        logger.info("Order %s payment succeeded", order_id)
    elif payment_status == "canceled":
        await order_service.update_status(
            order,
            status_name=OrderStatusName.CANCELED,
            payment_status=PaymentStatus.CANCELED,
            changed_by="yookassa",
        )
        logger.info("Order %s payment canceled", order_id)

    return {"status": "ok"}


@router.post("/test/simulate/{order_id}")
async def simulate_payment(
    order_id: int,
    session: AsyncSession = Depends(get_db),
):
    """Симуляция оплаты для тестирования. Доступен только в dev-окружении."""
    if app_settings.APP_ENV == "production":
        raise HTTPException(status_code=403, detail="Недоступно в production")

    order_service = OrderService(session)
    order = await order_service.get_by_id(order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    await order_service.update_status(
        order,
        status_name=OrderStatusName.NEW,
        payment_status=PaymentStatus.SUCCEEDED,
        changed_by="test",
    )

    return {"status": "ok", "order_id": order_id}
