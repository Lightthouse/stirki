import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db, get_current_client
from src.models.client import Client
from src.repositories.client import ClientRepository
from src.repositories.service import ServiceRepository
from src.schemas.order import CreateOrderIn, OrderOut, OrderListOut
from src.schemas.payment import PaymentOut
from src.services.order import OrderService
from src.services.pricing import PricingService
from src.services.payment import PaymentService
from src.settings import AppSettings
from src.enums import OrderStatusName, PaymentStatus

logger = logging.getLogger(__name__)

router = APIRouter()


def _order_services_list(order) -> list[str]:
    """Extract active service slugs from order boolean flags."""
    flags = {
        "ironing": order.ironing,
        "conditioner": order.conditioner,
        "vacuum_pack": order.vacuum_pack,
        "stain_remover": order.stain_remover,
        "wash_bag": order.wash_bag,
        "bleach": order.bleach,
        "color_catcher_sheets": order.color_catcher_sheets,
    }
    return [slug for slug, active in flags.items() if active]


@router.post("", response_model=PaymentOut)
async def create_order(
    body: CreateOrderIn,
    client: Client = Depends(get_current_client),
    session: AsyncSession = Depends(get_db),
):
    # Обновляем адрес клиента
    client_repo = ClientRepository(session)
    await client_repo.update(
        client,
        street=body.street,
        house=body.house,
        apartment=body.apartment,
        entrance=body.entrance,
        floor=body.floor,
    )

    # Рассчитываем цену
    service_repo = ServiceRepository(session)
    all_services = await service_repo.get_all_active()
    base_price = await service_repo.get_base_price()
    pricing = PricingService(base_price, all_services)

    total_price = 0 if body.is_free else pricing.calculate_order_price(body.bags_number, body.services, body.washing_type)
    service_flags = pricing.service_flags(body.services)

    # Создаём заказ
    app_settings = AppSettings()
    order_service = OrderService(session)

    if body.is_free or app_settings.APP_ENV != "production":
        # Бесплатный заказ (рекламный тариф) или dev-режим: без оплаты, сразу NEW
        order = await order_service.create(
            client=client,
            washing_type=body.washing_type,
            bags_number=body.bags_number,
            services=service_flags,
            total_price_rub=total_price,
            status_name=OrderStatusName.NEW,
            comment=body.comment,
            is_free=body.is_free,
        )
        changed_by = "free-tariff" if body.is_free else "dev-auto"
        await order_service.update_status(
            order,
            status_name=OrderStatusName.NEW,
            payment_status=PaymentStatus.SUCCEEDED,
            changed_by=changed_by,
        )
        confirmation_url = None
    else:
        # Платный заказ в продакшне: создаём платёж YooKassa
        order = await order_service.create(
            client=client,
            washing_type=body.washing_type,
            bags_number=body.bags_number,
            services=service_flags,
            total_price_rub=total_price,
            status_name=OrderStatusName.WAITING_FOR_CAPTURE,
            comment=body.comment,
            is_free=False,
        )
        confirmation_url = None
        try:
            payment_service = PaymentService()
            payment_result = payment_service.create_payment(
                amount=total_price,
                order_id=order.id,
                description=f"Стирки ON — заказ #{order.id}",
                customer_email=client.email or None,
            )
            await order_service.update_payment(
                order,
                yookassa_payment_id=payment_result["payment_id"],
                yookassa_confirmation_url=payment_result.get("confirmation_url"),
            )
            confirmation_url = payment_result.get("confirmation_url")
        except Exception:
            logger.exception("Failed to create YooKassa payment for order %s", order.id)

    return PaymentOut(
        order_id=order.id,
        total_price_rub=total_price,
        confirmation_url=confirmation_url,
    )


@router.get("", response_model=list[OrderListOut])
async def list_orders(
    client: Client = Depends(get_current_client),
    session: AsyncSession = Depends(get_db),
):
    order_service = OrderService(session)
    orders = await order_service.get_by_client_id(client.id)
    return [
        OrderListOut(
            id=o.id,
            status=o.status.name,
            total_price_rub=o.total_price_rub,
            payment_status=o.payment_status,
            washing_type=o.washing_type,
            bags_number=o.bags_number,
            created_at=o.created_at,
        )
        for o in orders
    ]


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: int,
    client: Client = Depends(get_current_client),
    session: AsyncSession = Depends(get_db),
):
    order_service = OrderService(session)
    order = await order_service.get_by_id(order_id)

    if not order or order.client_id != client.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден",
        )

    return OrderOut(
        id=order.id,
        status=order.status.name,
        street=order.street,
        house=order.house,
        apartment=order.apartment,
        entrance=order.entrance,
        floor=order.floor,
        washing_type=order.washing_type,
        bags_number=order.bags_number,
        services=_order_services_list(order),
        total_price_rub=order.total_price_rub,
        payment_status=order.payment_status,
        yookassa_confirmation_url=order.yookassa_confirmation_url,
        comment=order.comment,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )
