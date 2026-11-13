"""Email-уведомления операторам о новых заказах.

Отправка — best effort: выполняется в фоне (thread pool), ошибки только логируются
и никогда не ломают создание/оплату заказа.
"""

import asyncio
import logging
import smtplib
from email.message import EmailMessage

from sqlalchemy.ext.asyncio import AsyncSession

from src.addresses import STREETS_SLUG
from src.models.client import Client
from src.models.order import Order
from src.repositories.service import ServiceRepository
from src.services.schedule import MSK
from src.settings import SmtpSettings

logger = logging.getLogger(__name__)

_SLUG_TO_STREET = {slug: name for name, slug in STREETS_SLUG.items()}


def _recipients(settings: SmtpSettings) -> list[str]:
    """NOTIFY_EMAIL — один или несколько адресов через запятую."""
    return [a.strip() for a in settings.NOTIFY_EMAIL.split(",") if a.strip()]


def _build_message(
    order: Order, client: Client, service_names: dict[str, str], settings: SmtpSettings,
) -> EmailMessage:
    street = _SLUG_TO_STREET.get(order.street, order.street)
    services = ", ".join(service_names.get(s, s) for s in order.service_slugs) or "нет"
    created = order.created_at.astimezone(MSK).strftime("%d.%m.%Y %H:%M") if order.created_at else ""

    lines = [
        f"Новый заказ № {order.number} ({created} МСК)",
        "",
        f"Клиент: {client.name or '—'}, {client.phone}",
        f"Адрес: {street}, д. {order.house}, подъезд {order.entrance}, этаж {order.floor}, кв. {order.apartment}",
        f"Комментарий: {order.comment or '—'}",
        "",
        f"Пакетов: {order.bags_number}, вещей: {order.pieces_number}",
        f"Допуслуги: {services}",
    ]
    if order.is_free:
        lines.append("Тариф: бесплатный")
    else:
        lines.append(f"Тариф: платный, оплачено {order.total_price_rub} ₽")
        # По этому номеру платёж ищется в реестре Точки, а заказ — в поиске админки.
        lines.append(f"Платёж в Точке: {order.payment_link_id or '—'}")

    msg = EmailMessage()
    msg["Subject"] = f"Новый заказ {order.number} — {street}, {order.house}"
    msg["From"] = settings.SMTP_USER
    msg["To"] = ", ".join(_recipients(settings))
    msg.set_content("\n".join(lines))
    return msg


def _send(msg: EmailMessage, settings: SmtpSettings) -> None:
    try:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as smtp:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(msg)
        logger.info("Уведомление о заказе отправлено: %s", msg["Subject"])
    except Exception:
        logger.exception("Не удалось отправить email-уведомление: %s", msg["Subject"])


async def notify_new_order(session: AsyncSession, order: Order, client: Client) -> None:
    """Поставить отправку письма в фон. Не ждёт отправки и не бросает исключений."""
    settings = SmtpSettings()
    if not (settings.SMTP_HOST and settings.SMTP_USER and _recipients(settings)):
        logger.warning("SMTP не настроен — уведомление о заказе %s не отправлено", order.id)
        return
    try:
        # Названия допуслуг — из таблицы services, как их видят сотрудники в админке.
        service_names = await ServiceRepository(session).get_names(order.service_slugs)
        msg = _build_message(order, client, service_names, settings)
        asyncio.get_running_loop().run_in_executor(None, _send, msg, settings)
    except Exception:
        logger.exception("Не удалось подготовить email-уведомление о заказе %s", order.id)
