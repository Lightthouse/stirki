# src/services/kanban.py
import asyncio
import logging
from typing import Optional

from trello import TrelloClient, Label

from src.database import settings
from src.models import Order

logger = logging.getLogger(__name__)


class Kanban:
    """
    Kanban сервис — wrapper над py-trello TrelloClient.
    Хранит клиент как class var и предоставляет classmethods:
      - configure(settings)  -> инициализировать client и default list
      - create_card_sync(...) -> создаёт карточку синхронно (blocking)
      - create_card_async(...) -> async wrapper (to_thread)
      - enqueue_create_card(order, total) -> fire-and-forget job
    """

    BOARD_ID = 'RGuiWOAZ'
    LIST_ID = '6937fbac2dcd2ca31a7e3f0a'
    EXTRA_LABELS = {
        "need_ironing": "693bf869f3ad524b92ff435d",
        "need_conditioner": "6937fad4cc2d6a1245d7b7be",
        "need_vacuum_pack": "693a9512b66b9a84869c2918",
        "need_uv": "6937fce76955bed06e42984f",
        "need_wash_bag": "6937fad4cc2d6a1245d7b7c0",
    }

    _client: Optional[TrelloClient] = None
    _default_list_id: Optional[str] = '6937fbac2dcd2ca31a7e3f0a'
    _configured: bool = False

    @classmethod
    def configure(cls) -> None:
        """
        Инициализация: передать Pydantic settings или другой объект с атрибутами:
        TRELLO_KEY, TRELLO_TOKEN, TRELLO_DEFAULT_LIST_ID.
        Вызывать один раз при старте процесса.
        """
        key = ''
        token = ''

        cls._client = TrelloClient(api_key=key, token=token)
        cls._configured = True

        logger.info("Kanban configured. default_list_id=%s", cls._default_list_id)

    @classmethod
    def _is_configured(cls) -> bool:
        return cls._configured and cls._client is not None

    @classmethod
    def create_card_sync(cls, order: Order) -> Optional[str]:
        """
        Blocking call — использует py-trello синхронно.
        Возвращает id карточки или None при ошибке / если не настроено.
        """
        if not cls._is_configured():
            logger.debug("Kanban.create_card_sync: not configured, skipping create")
            return None

        name = cls._build_name(order)
        desc = cls._build_desc(order)
        # labels = cls._get_extra_labels(order)


        try:
            trello_list = cls._client.get_list(cls.LIST_ID)
            card = trello_list.add_card(name, desc)

            return getattr(card, "id", None)
        except Exception:
            logger.exception("Kanban.create_card_sync: failed to create card")
            return None

    @classmethod
    async def create_card_async(cls, order: Order) -> Optional[str]:
        # run blocking call in a thread
        return await asyncio.to_thread(cls.create_card_sync, order)

    @classmethod
    def _build_name(cls, order: Order) -> str:
        return f"#{order.id} {order.client.name or order.client.phone}"

    @classmethod
    def _build_desc(cls, order: Order) -> str:
        street_name = order.street.name if getattr(order, "street", None) else getattr(order, "street_id", "")
        return (
            f"Заказа #{order.id}\n"
            f"Адрес: {street_name}, дом {order.house or ''}, квартира 228, подъезд {order.entrance or '—'}, этаж {order.floor or '—'}\n"
            f"Телефон: {order.client.phone or '—'}\n"
            f"Имя: {order.client.name or '—'}\n"
            f"Телеграм id: {order.client.telegram_id or '—'}\n"
            f"Стоимость: {order.total_price_rub} руб\n"
            f"Комментарий: {order.comment or '—'}\n"
            f"Допы\n"
            f"=================================================\n"
            f"Глажка: {'Да' if order.need_ironing else 'Нет'}\n"
            f"Кондиционер: {'Да' if order.need_conditioner else 'Нет'}\n"
            f"Вакуумный пакет: {'Да' if order.need_vacuum_pack else 'Нет'}\n"
            f"Ультрафиолет: {'Да' if order.need_uv else 'Нет'}\n"
            f"Мешок для стирки: {'Да' if order.need_wash_bag else 'Нет'}\n"
            f"=================================================\n"
        )

    @classmethod
    def _get_extra_labels(cls, order: Order) -> list[str]:
        """Возвращает список ID лейблов для включённых допов"""
        labels = []
        mapping = cls.EXTRA_LABELS
        if order.need_ironing:
            labels.append(mapping["need_ironing"])
        if order.need_conditioner:
            labels.append(mapping["need_conditioner"])
        if order.need_vacuum_pack:
            labels.append(mapping["need_vacuum_pack"])
        if order.need_uv:
            labels.append(mapping["need_uv"])
        if order.need_wash_bag:
            labels.append(mapping["need_wash_bag"])
        return labels

    @classmethod
    def enqueue_create_card(cls, order: Order) -> None:
        """
        Fire-and-forget: создаёт фоновую задачу, которая создаст карточку и обновит order.trello_card_id.
        Нужно вызывать из async-контекста (create_task стартуется здесь).
        """

        async def _job():
            try:
                card_id = await cls.create_card_async(order)
                if card_id:
                    # обновлять лучше через свежий объект, чтобы избежать stale relations
                    fresh = await Order.get(id=order.id)
                    fresh.trello_card_id = card_id
                    await fresh.save(update_fields=["trello_card_id"])
                    logger.info("Attached trello_card_id=%s to order %s", card_id, order.id)
            except Exception:
                logger.exception("Kanban.enqueue_create_card job failed for order %s", order.id)

        # fire and forget
        asyncio.create_task(_job())


