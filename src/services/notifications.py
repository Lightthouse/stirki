"""Email-уведомления операторам: новые заказы и сбои при создании платежа.

Отправка — best effort: выполняется в фоне (thread pool), ошибки только логируются
и никогда не ломают создание/оплату заказа.
"""

import asyncio
import logging
import re
import smtplib
from email.message import EmailMessage

from sqlalchemy.ext.asyncio import AsyncSession

from src.addresses import STREETS_SLUG
from src.enums import Handover
from src.models.client import Client
from src.models.order import Order
from src.repositories.service import ServiceRepository
from src.repositories.system_settings import get_system_settings
from src.services.schedule import MSK
from src.settings import SmtpSettings

logger = logging.getLogger(__name__)

_SLUG_TO_STREET = {slug: name for name, slug in STREETS_SLUG.items()}


def parse_email_list(value: str) -> list[str]:
    """Адреса через запятую (точку с запятой, пробел или перевод строки) — в список без пустых."""
    return [a for a in re.split(r"[,;\s]+", value or "") if a]


async def _recipients(session: AsyncSession) -> list[str]:
    """Получатели писем — из админки («Системные настройки»), меняются без перезапуска."""
    return parse_email_list((await get_system_settings(session)).notify_emails)


def _build_message(
    order: Order, client: Client, service_names: dict[str, str], settings: SmtpSettings, recipients: list[str],
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
        "Доставка: на следующий день (заказ оформлен вечером)" if order.next_day_delivery else "Доставка: сегодня",
        f"Передача: {Handover(order.handover).label}",
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
    msg["To"] = ", ".join(recipients)
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
    try:
        recipients = await _recipients(session)
        if not (settings.SMTP_HOST and settings.SMTP_USER and recipients):
            logger.warning("SMTP или получатели не настроены — уведомление о заказе %s не отправлено", order.id)
            return
        # Названия допуслуг — из таблицы services, как их видят сотрудники в админке.
        service_names = await ServiceRepository(session).get_names(order.service_slugs)
        msg = _build_message(order, client, service_names, settings, recipients)
        asyncio.get_running_loop().run_in_executor(None, _send, msg, settings)
    except Exception:
        logger.exception("Не удалось подготовить email-уведомление о заказе %s", order.id)


async def notify_payment_failed(session: AsyncSession, order: Order, client: Client, error: str) -> None:
    """Письмо операторам: клиент не смог перейти к оплате (Точка не выдала ссылку).

    Клиенту в этот момент показывается ошибка, заказ отменён и скрыт из его истории —
    без письма о сломанной оплате никто бы не узнал. Не бросает исключений.
    """
    settings = SmtpSettings()
    try:
        recipients = await _recipients(session)
        if not (settings.SMTP_HOST and settings.SMTP_USER and recipients):
            logger.warning("SMTP или получатели не настроены — письмо о сбое оплаты заказа %s не отправлено", order.id)
            return
        msg = EmailMessage()
        msg["Subject"] = f"Сбой оплаты: заказ {order.number} не оформлен"
        msg["From"] = settings.SMTP_USER
        msg["To"] = ", ".join(recipients)
        msg.set_content("\n".join([
            f"Клиент не смог перейти к оплате заказа № {order.number} на {order.total_price_rub} ₽:",
            "не удалось создать ссылку на оплату в Точке. Заказ автоматически отменён,",
            "деньги не списывались. Клиенту показана ошибка с контактами поддержки.",
            "",
            f"Клиент: {client.name or '—'}, {client.phone}",
            "",
            f"Ошибка: {error[:2000]}",
            "",
            "Подробности — в логах бэкенда: docker compose --profile prod logs backend",
        ]))
        asyncio.get_running_loop().run_in_executor(None, _send, msg, settings)
    except Exception:
        logger.exception("Не удалось подготовить письмо о сбое оплаты заказа %s", order.id)
