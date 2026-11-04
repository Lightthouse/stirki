import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db, get_current_client
from src.models.client import Client
from src.schemas.payment import PaymentOut
from src.services.order import OrderService
from src.services.payment_sync import sync_order_payment

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

    return {"status": await sync_order_payment(session, order)}


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
