import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db, get_current_client
from src.models.client import Client
from src.models.order import Order
from src.models.system_settings import SystemSettings as SystemSettingsModel
from src.repositories.client import ClientRepository
from src.repositories.order import OrderRepository
from src.repositories.service import ServiceRepository
from src.schemas.order import CreateOrderIn, OrderOut, OrderListOut
from src.schemas.payment import PaymentOut
from src.services.order import OrderService
from src.services.pricing import PricingService
from src.services.payment import PaymentService
from src.enums import OrderStatusName, PaymentStatus

logger = logging.getLogger(__name__)

router = APIRouter()



@router.post("", response_model=PaymentOut)
async def create_order(
    body: CreateOrderIn,
    client: Client = Depends(get_current_client),
    session: AsyncSession = Depends(get_db),
):
    order_repo = OrderRepository(session)
    if await order_repo.has_active_order(client.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="У вас уже есть активный заказ",
        )

    result = await session.execute(select(SystemSettingsModel).limit(1))
    sys_settings = result.scalar_one_or_none()

    if body.is_free and sys_settings is not None and not sys_settings.free_tariff_is_available:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Бесплатный тариф временно недоступен",
        )

    if sys_settings is not None:
        bag_limit = sys_settings.free_bag_slots if body.is_free else sys_settings.paid_bag_slots
        piece_limit = sys_settings.free_piece_slots if body.is_free else sys_settings.paid_piece_slots
        if body.bags_number > bag_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Превышен лимит пакетов: не более {bag_limit}",
            )
        if body.pieces_number > piece_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Превышен лимит вещей: не более {piece_limit}",
            )

    if body.bags_number > 0 and body.pieces_number > 0:
        washing_type = 'mixed'
    elif body.pieces_number > 0:
        washing_type = 'piece'
    else:
        washing_type = 'bag'

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

    total_price = 0 if body.is_free else pricing.calculate_order_price(body.bags_number, body.pieces_number, body.services)
    service_flags = Order.flags_from_slugs(body.services)

    order_service = OrderService(session)

    if body.is_free:
        order = await order_service.create(
            client=client,
            washing_type=washing_type,
            bags_number=body.bags_number,
            pieces_number=body.pieces_number,
            services=service_flags,
            total_price_rub=total_price,
            status_name=OrderStatusName.NEW,
            comment=body.comment,
            is_free=True,
        )
        await order_service.update_status(
            order,
            status_name=OrderStatusName.NEW,
            payment_status=PaymentStatus.SUCCEEDED,
            changed_by="free-tariff",
        )
        confirmation_url = None
    else:
        payment_token = str(uuid4())
        order = await order_service.create(
            client=client,
            washing_type=washing_type,
            bags_number=body.bags_number,
            pieces_number=body.pieces_number,
            services=service_flags,
            total_price_rub=total_price,
            status_name=OrderStatusName.NEW,
            comment=body.comment,
            is_free=False,
        )
        try:
            payment_service = PaymentService()
            payment_result = payment_service.create_payment(
                amount=total_price,
                payment_token=payment_token,
                purpose=f"Стирка ON — заказ #{order.id}",
            )
            confirmation_url = payment_result.get("payment_link")
            if not confirmation_url:
                raise ValueError("Payment link missing from Tochka response")
            await order_service.update_payment(
                order,
                operation_id=payment_result["operation_id"],
                payment_link=confirmation_url,
                payment_token=payment_token,
            )
        except Exception:
            logger.exception("Failed to create payment for order %s", order.id)
            await order_service.update_status(
                order,
                status_name=OrderStatusName.CANCELED,
                payment_status=PaymentStatus.CANCELED,
                changed_by="system",
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Не удалось создать платёж. Попробуйте ещё раз.",
            )

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
            status=o.status.slug,
            total_price_rub=o.total_price_rub,
            payment_status=o.payment_status,
            washing_type=o.washing_type,
            bags_number=o.bags_number,
            pieces_number=o.pieces_number,
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
        status=order.status.slug,
        street=order.street,
        house=order.house,
        apartment=order.apartment,
        entrance=order.entrance,
        floor=order.floor,
        washing_type=order.washing_type,
        bags_number=order.bags_number,
        pieces_number=order.pieces_number,
        services=order.service_slugs,
        total_price_rub=order.total_price_rub,
        payment_status=order.payment_status,
        is_free=order.is_free,
        comment=order.comment,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )
