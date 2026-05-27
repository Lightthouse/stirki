import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db, get_current_client
from src.enums import OrderStatusName, PaymentStatus
from src.models.client import Client
from src.schemas.payment import PaymentOut
from src.services.order import OrderService
from src.services.payment import PaymentService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/verify/{order_id}")
async def verify_payment(
    order_id: int,
    client: Client = Depends(get_current_client),
    session: AsyncSession = Depends(get_db),
):
    """Проверить статус оплаты через Точка Банк и обновить заказ."""
    order_service = OrderService(session)
    order = await order_service.get_by_id(order_id)

    if not order or order.client_id != client.id:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    if order.payment_status == PaymentStatus.SUCCEEDED:
        return {"status": "approved"}

    if not order.operation_id:
        return {"status": "pending"}

    try:
        payment_service = PaymentService()
        payment_info = payment_service.get_payment(order.operation_id)
        operations = payment_info.get("Data", {}).get("Operation", [])
        if not operations:
            return {"status": "pending"}

        tochka_status = operations[0].get("status", "").upper()

        if tochka_status == "APPROVED":
            await order_service.update_status(
                order,
                status_name=OrderStatusName.COURIER_PICKUP,
                payment_status=PaymentStatus.SUCCEEDED,
                changed_by="tochka",
            )
            return {"status": "approved"}
        elif tochka_status in ("REJECTED", "EXPIRED"):
            await order_service.update_status(
                order,
                status_name=OrderStatusName.CANCELED,
                payment_status=PaymentStatus.CANCELED,
                changed_by="tochka",
            )
            return {"status": "rejected"}
        else:
            return {"status": "pending"}
    except Exception:
        logger.exception("Failed to verify payment for order %s", order_id)
        return {"status": "pending"}


@router.get("/by-token/{payment_token}", response_model=PaymentOut)
async def get_order_by_payment_token(
    payment_token: str,
    client: Client = Depends(get_current_client),
    session: AsyncSession = Depends(get_db),
):
    """Получить заказ по payment_token после редиректа с оплаты."""
    order_service = OrderService(session)
    order = await order_service.get_by_payment_token(payment_token)

    if not order or order.client_id != client.id:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    return PaymentOut(
        order_id=order.id,
        total_price_rub=order.total_price_rub,
        confirmation_url=None,
    )
