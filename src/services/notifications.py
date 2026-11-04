"""Email-уведомления операторам о новых заказах.

Отправка — best effort: выполняется в фоне (thread pool), ошибки только логируются
и никогда не ломают создание/оплату заказа.
"""

import asyncio
import logging
import smtplib
from email.message import EmailMessage

from src.addresses import STREETS_SLUG
from src.models.client import Client
from src.models.order import Order
from src.services.schedule import MSK
from src.settings import SmtpSettings

logger = logging.getLogger(__name__)

_SLUG_TO_STREET = {slug: name for name, slug in STREETS_SLUG.items()}

SERVICE_NAMES = {
    "ironing": "Глажка",
    "conditioner": "Кондиционер",
    "vacuum_pack": "Вакуумный пакет",
    "stain_remover": "Пятновыводитель",
    "wash_bag": "Мешок для стирки",
    "bleach": "Отбеливатель",
    "color_catcher_sheets": "Салфетки против окрашивания",
}


def _build_message(order: Order, client: Client, settings: SmtpSettings) -> EmailMessage:
    street = _SLUG_TO_STREET.get(order.street, order.street)
    services = ", ".join(SERVICE_NAMES.get(s, s) for s in order.service_slugs) or "нет"
    tariff = "бесплатный" if order.is_free else f"платный, оплачено {order.total_price_rub} ₽"
    created = order.created_at.astimezone(MSK).strftime("%d.%m.%Y %H:%M") if order.created_at else ""

    body = "\n".join([
        f"Новый заказ № ST-{order.id} ({created} МСК)",
        "",
        f"Клиент: {client.name or '—'}, {client.phone}",
        f"Адрес: {street}, д. {order.house}, подъезд {order.entrance}, этаж {order.floor}, кв. {order.apartment}",
        f"Комментарий: {order.comment or '—'}",
        "",
        f"Пакетов: {order.bags_number}, вещей: {order.pieces_number}",
        f"Допуслуги: {services}",
        f"Тариф: {tariff}",
    ])

    msg = EmailMessage()
    msg["Subject"] = f"Новый заказ ST-{order.id} — {street}, {order.house}"
    msg["From"] = settings.SMTP_USER
    msg["To"] = settings.NOTIFY_EMAIL
    msg.set_content(body)
    return msg


def _send(msg: EmailMessage, settings: SmtpSettings) -> None:
    try:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as smtp:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(msg)
        logger.info("Уведомление о заказе отправлено: %s", msg["Subject"])
    except Exception:
        logger.exception("Не удалось отправить email-уведомление: %s", msg["Subject"])


def notify_new_order(order: Order, client: Client) -> None:
    """Поставить отправку письма в фон. Не блокирует и не бросает исключений."""
    settings = SmtpSettings()
    if not (settings.SMTP_HOST and settings.SMTP_USER and settings.NOTIFY_EMAIL):
        logger.warning("SMTP не настроен — уведомление о заказе %s не отправлено", order.id)
        return
    try:
        msg = _build_message(order, client, settings)
        asyncio.get_running_loop().run_in_executor(None, _send, msg, settings)
    except Exception:
        logger.exception("Не удалось подготовить email-уведомление о заказе %s", order.id)
