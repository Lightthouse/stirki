import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.enums import KaitenColumns
from src.repositories.order import OrderRepository
from src.services.order import OrderService
from src.settings import KaitenSettings

logger = logging.getLogger(__name__)

router = APIRouter()

# Обратный маппинг: column_id (str) → status_name
_COLUMN_TO_STATUS: dict[str, str] = {
    str(v): k.lower()
    for k, v in KaitenColumns.__members__.items()
}


@router.post("/kaiten-webhook")
async def kaiten_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_kaiten_token: str | None = Header(default=None),
):
    settings = KaitenSettings()

    # Проверка секрета (если задан в .env)
    if settings.WEBHOOK_SECRET and x_kaiten_token != settings.WEBHOOK_SECRET:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")

    body = await request.json()
    logger.info("Kaiten webhook payload: %s", body)

    # Извлекаем card_id и column_id из payload
    # Kaiten отправляет: {"data": {"id": <card_id>, "column_id": <column_id>}, ...}
    try:
        data = body.get("data") or body
        card_id = int(data["id"])
        column_id = str(data["column_id"])
    except (KeyError, TypeError, ValueError):
        logger.warning("Kaiten webhook: не удалось разобрать payload: %s", body)
        return {"status": "ignored", "reason": "unrecognized payload format"}

    # Ищем заказ по kaiten_card_id
    repo = OrderRepository(db)
    order = await repo.get_by_kaiten_card_id(card_id)
    if not order:
        logger.info("Kaiten webhook: карточка %s не привязана ни к одному заказу", card_id)
        return {"status": "ignored", "reason": "order not found"}

    # Определяем новый статус
    status_name = _COLUMN_TO_STATUS.get(column_id)
    if not status_name:
        logger.info("Kaiten webhook: колонка %s не соответствует ни одному статусу", column_id)
        return {"status": "ignored", "reason": "unknown column"}

    if order.status and order.status.name == status_name:
        return {"status": "ignored", "reason": "status unchanged"}

    # Обновляем статус, не трогая Kaiten (skip_kaiten=True — без цикла)
    order_service = OrderService(db)
    await order_service.update_status(
        order,
        status_name=status_name,
        changed_by="kaiten",
        skip_kaiten=True,
    )

    logger.info("Kaiten webhook: заказ %s → статус %s", order.id, status_name)
    return {"status": "ok", "order_id": order.id, "new_status": status_name}
