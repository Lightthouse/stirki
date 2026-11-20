import asyncio
import logging
import secrets
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.addresses import HOUSE_STREET_MAP, STREETS_SLUG
from src.api.dependencies import get_db, get_current_client
from src.enums import OrderStatusName, PaymentStatus
from src.models.client import Client
from src.models.order import Order
from src.repositories.order import OrderRepository
from src.repositories.service import ServiceRepository
from src.repositories.system_settings import get_system_settings
from src.schemas.order import CreateOrderIn, OrderOut, OrderListOut
from src.schemas.payment import PaymentOut
from src.services.notifications import notify_new_order, notify_payment_failed
from src.services.order import OrderService
from src.services.payment import PaymentService
from src.services.payment_sync import sync_order_payment
from src.services.pricing import EXCLUSIVE_ADDONS, PricingService
from src.services.schedule import (
    accept_hours_text, is_accepting_orders, is_next_day_delivery, start_of_today_msk,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Заказ при этом отменяется и скрывается из истории клиента (OrderRepository.get_by_client_id).
PAYMENT_FAILED_DETAIL = "Не удалось перейти к оплате. Деньги не списаны, заказ не оформлен."

_SLUG_TO_STREET = {slug: name for name, slug in STREETS_SLUG.items()}

# Без похожих символов (0/O, 1/I/L), чтобы номер можно было продиктовать.
_LINK_ID_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"


def _new_payment_link_id(order: Order) -> str:
    """paymentLinkId для Точки: номер заказа + случайный хвост, например ST-123-K7Q2.

    Точка требует уникальности paymentLinkId навсегда, а orders.id повторяется: локальная
    разработка ходит в ту же Точку, а БД пересоздаётся и нумерация начинается с 1.
    """
    tail = "".join(secrets.choice(_LINK_ID_ALPHABET) for _ in range(4))
    return f"{order.number}-{tail}"


def _is_address_in_zone(street_slug: str, house: str) -> bool:
    street_name = _SLUG_TO_STREET.get(street_slug)
    return street_name is not None and house in HOUSE_STREET_MAP.get(street_name, [])


@router.post("", response_model=PaymentOut)
async def create_order(
    body: CreateOrderIn,
    client: Client = Depends(get_current_client),
    session: AsyncSession = Depends(get_db),
):
    # Сериализуем создание заказа по client_id: advisory-блокировка держится до коммита
    # транзакции (вставки заказа ниже), поэтому конкурентный запрос дождётся её, увидит
    # уже созданный заказ в has_active_order и получит 409 вместо дубля.
    await session.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": client.id})

    sys_settings = await get_system_settings(session)

    if not is_accepting_orders(sys_settings):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Заказы принимаются ежедневно {accept_hours_text(sys_settings)}",
        )

    if not _is_address_in_zone(body.street, body.house):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Этот адрес пока не входит в зону обслуживания",
        )

    if body.bags_number + body.pieces_number == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Добавьте в заказ хотя бы одну позицию",
        )

    order_repo = OrderRepository(session)
    if await order_repo.has_active_order(client.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="У вас уже есть активный заказ",
        )

    if body.is_free and not sys_settings.free_tariff_is_available:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Бесплатный тариф временно недоступен",
        )

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

    if body.is_free:
        free_today = await order_repo.count_free_orders_for_address_since(
            body.street, body.house, body.apartment, start_of_today_msk(),
        )
        if free_today >= sys_settings.free_orders_per_address_per_day:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Бесплатный заказ на этот адрес сегодня уже оформлен. "
                       "Следующий можно будет оформить завтра или выбрать платный тариф",
            )

    # Время оформления фиксируем в заказе: после смены настройки в админке срок старых заказов не меняется.
    next_day = is_next_day_delivery(sys_settings)

    if body.bags_number > 0 and body.pieces_number > 0:
        washing_type = 'mixed'
    elif body.pieces_number > 0:
        washing_type = 'piece'
    else:
        washing_type = 'bag'

    # Обновляем адрес клиента в памяти — будет закоммичено вместе с заказом.
    client.street = body.street
    client.house = body.house
    client.apartment = body.apartment
    client.entrance = body.entrance
    client.floor = body.floor

    order_service = OrderService(session)

    # Бесплатный тариф: допуслуги недоступны — игнорируем body.services,
    # чтобы платные опции не прикреплялись к заказу за 0 ₽.
    if body.is_free:
        order = await order_service.create(
            client=client,
            washing_type=washing_type,
            bags_number=body.bags_number,
            pieces_number=body.pieces_number,
            services=Order.flags_from_slugs([]),
            total_price_rub=0,
            status_name=OrderStatusName.COURIER_PICKUP,
            comment=body.comment,
            is_free=True,
            next_day_delivery=next_day,
            handover=body.handover,
            payment_status=PaymentStatus.SUCCEEDED,
        )
        await notify_new_order(session, order, client)
        return PaymentOut(order_id=order.id, total_price_rub=0, confirmation_url=None)

    # Кассовый чек Точка отправляет только на email — без него платёж не создать. Клиент вводит его в корзине
    # (там подставлен прошлый); старый фронтенд из кэша браузера email не присылает — тогда берём сохранённый.
    email = body.email or client.email
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Укажите email для чека",
        )
    # Сохраняется вместе с заказом и подставится в корзину в следующий раз.
    client.email = email

    service_repo = ServiceRepository(session)
    pricing = PricingService(await service_repo.get_all_active(), sys_settings)
    # Только допы, которые сейчас предлагаются: выключенный в админке доп не попадёт в заказ бесплатно.
    addon_slugs = pricing.selected_addons(body.services)
    for pair in EXCLUSIVE_ADDONS:
        if all(slug in addon_slugs for slug in pair):
            names = " и ".join(f"«{pricing.name(slug)}»" for slug in pair)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Нельзя выбрать вместе {names}",
            )
    lines = pricing.order_lines(body.bags_number, body.pieces_number, addon_slugs)
    total_price = sum(line.total for line in lines)

    payment_token = str(uuid4())
    order = await order_service.create(
        client=client,
        washing_type=washing_type,
        bags_number=body.bags_number,
        pieces_number=body.pieces_number,
        services=Order.flags_from_slugs(addon_slugs),
        total_price_rub=total_price,
        status_name=OrderStatusName.WAITING_PAYMENT,
        comment=body.comment,
        is_free=False,
        next_day_delivery=next_day,
        handover=body.handover,
        bag_price_rub=pricing.base_price,
        piece_price_rub=pricing.piece_price,
    )
    payment_link_id = _new_payment_link_id(order)
    try:
        payment_result = await asyncio.to_thread(
            PaymentService().create_payment,
            lines=lines,
            payment_token=payment_token,
            payment_link_id=payment_link_id,
            order_number=order.number,
            email=client.email,
            client_name=client.name,
            purpose=f"Стирка ON — заказ № {order.number}",
        )
        confirmation_url = payment_result.get("payment_link")
        if not confirmation_url:
            raise ValueError("Payment link missing from Tochka response")
        await order_service.update_payment(
            order,
            operation_id=payment_result["operation_id"],
            payment_link=confirmation_url,
            payment_token=payment_token,
            payment_link_id=payment_link_id,
        )
    except Exception as e:
        logger.exception("Failed to create payment for order %s", order.id)
        await order_service.update_status(
            order,
            status_name=OrderStatusName.CANCELED,
            payment_status=PaymentStatus.CANCELED,
            changed_by="system",
        )
        # Ответ Точки (код и текст ошибки) полезнее операторам, чем repr исключения.
        if isinstance(e, httpx.HTTPStatusError):
            error = f"{e.response.status_code}: {e.response.text}"
        else:
            error = repr(e)
        await notify_payment_failed(session, order, client, error)
        # Текст сверяется на фронтенде (OrderPage.tsx) — там к нему добавляются контакты поддержки.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=PAYMENT_FAILED_DETAIL,
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
    for o in orders:
        if o.status.slug == OrderStatusName.WAITING_PAYMENT:
            await sync_order_payment(session, o)
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

    waiting = order.status.slug == OrderStatusName.WAITING_PAYMENT
    if waiting:
        await sync_order_payment(session, order)
        waiting = order.status.slug == OrderStatusName.WAITING_PAYMENT

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
        bag_price_rub=order.bag_price_rub,
        piece_price_rub=order.piece_price_rub,
        payment_status=order.payment_status,
        is_free=order.is_free,
        next_day_delivery=order.next_day_delivery,
        handover=order.handover,
        comment=order.comment,
        payment_link=order.payment_link if waiting else None,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )
