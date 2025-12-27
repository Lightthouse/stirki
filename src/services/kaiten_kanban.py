import logging
import httpx
from typing import Any, Dict, Optional

from src.settings import KaitenSettings
from src.enums import KaitenColumns, KaitenTagsNames, KaitenTagsIds
from src.models import Order

logger = logging.getLogger(__name__)


class KaitenAPIError(Exception):
    """Базовое исключение для ошибок Kaiten API."""

    def __init__(self, response: httpx.Response, message: str | None = None):
        self.status_code = response.status_code
        self.response_text = response.text
        try:
            self.json = response.json()
        except ValueError:
            self.json = None
        super().__init__(message or f"Kaiten API error {response.status_code}: {response.text}")


class Kaiten:
    def __init__(
            self,
            timeout: float = 30.0,
    ):
        self.settings = KaitenSettings()

        self.base_url = f'https://{self.settings.DOMAIN}.kaiten.ru/api/latest'
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.settings.API_KEY}",
        }

        self.client = httpx.Client(
            base_url=self.base_url,
            headers=self.headers,
            timeout=timeout,
            follow_redirects=True,
        )

    def _raise_for_status(self, response: httpx.Response) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise KaitenAPIError(response) from exc

    def add_tags_to_card(
            self,
            card_id: int,
            tag: KaitenTagsNames
    ):
        """
        Добавление тэга к карточки.
        Почему-то можно добавлять только по 1 тэгу за раз.

        :param card_id:
        :param tag:
        :return:
        """
        response = self.client.post(f"/cards/{card_id}/tags", json={'name': tag})
        self._raise_for_status(response)
        return response.json()

    def change_card_status(
            self,
            card_id: int,
            status: KaitenColumns = KaitenColumns.NEW,
    ):
        response = self.client.patch(f"/cards/{card_id}", json={'column_id': status})
        self._raise_for_status(response)
        return response.json()

    def create_card(
            self,
            title: str,
            description: str = '',
            column_id: int = KaitenColumns.WAITING_FOR_CAPTURE,
            owner_id: int | None = None,
            responsible_id: int | None = None,
            due_date: str | None = None,  # формат YYYY-MM-DD
            tags: list[dict[str, KaitenTagsNames]] | None = None,
    ) -> Dict[str, Any]:
        """
        Создаёт новую карточку в указанной колонке.

        Основные обязательные поля: title, board_id, column_id.
        Остальные — по необходимости (см. пример curl).
        """
        payload: Dict[str, Any] = {
            "title": title,
            "description": description,
            "board_id": self.settings.BOARD,
            "column_id": column_id,
            "expires_later": False,
        }

        if owner_id:
            payload["owner_id"] = owner_id
        if responsible_id:
            payload["responsible_id"] = responsible_id
        if due_date:
            payload["due_date"] = due_date
            payload["due_date_time_present"] = False  # если нет времени
        if tags:
            payload["tags"] = tags

        response = self.client.post("/cards", json=payload)
        self._raise_for_status(response)
        return response.json()

    def get_board_columns(self) -> list[Dict[str, Any]]:
        """Получить список колонок на доске — удобно для поиска column_id по названию."""
        response = self.client.get(f"/boards/{self.settings.BOARD}/columns")
        self._raise_for_status(response)
        return response.json()

    def get_card(self, card_id: int) -> Dict[str, Any]:
        response = self.client.get(f"/cards/{card_id}")
        self._raise_for_status(response)
        return response.json()

    def get_tags(self) -> list[Dict[str, Any]]:
        """Получить все теги (для поиска tag_id по названию)."""
        response = self.client.get("/tags")
        self._raise_for_status(response)
        return response.json()

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> Kaiten:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


    @classmethod
    def _maker_descriptions(
            cls,
            title: str,
            options: dict[KaitenTagsNames, bool],
            order: Order
    ) -> str:
        """
        Формирование описание заказа.
        :param order:
        :return:
        """
        street_name = order.street.name if getattr(order, "street", None) else getattr(order, "street_id", "")

        option_num = 1
        option_text = ""
        for op_name, op_status in options.items():
            if not op_status:
                continue
            option_text += f'{option_num}. {op_name.capitalize()}\n'
            option_num +=1

        return (
            f"{title}\n"
            f"- Адрес: {street_name}, дом {order.house or ''}, квартира {order.apartment}, подъезд {order.entrance or '—'}, этаж {order.floor or '—'}\n"
            f"- Телефон: {order.client.phone or '—'}\n"
            f"- Имя: {order.client.name or '—'}\n"
            f"- Телеграм id: {order.client.telegram_id or '—'}\n"
            f"- Стоимость: {order.total_price_rub} руб\n"
            f"- Комментарий: {order.comment or '—'}\n\n"
            f"**Дополнительно**\n"
            f"{option_text}"
        )


    async def add_card_to_order(self, order: Order) -> int:
        """
        Создание карточки с доставкой и добавление её id в заказ.
        :param order:
        :return:
        """

        options = {
            KaitenTagsNames.IRONING: order.ironing,
            KaitenTagsNames.UV: order.uv,
            KaitenTagsNames.VACUUM_PACK: order.vacuum_pack,
            KaitenTagsNames.WASH_BAG: order.wash_bag,
            KaitenTagsNames.CONDITIONER: order.conditioner,
            KaitenTagsNames.EXACT_TIME: order.delivery_exact_time,
        }
        tags = [{'name': op_name} for op_name, op_status in options.items() if op_status]
        title = f'Заказ #{order.id}'
        description = self._maker_descriptions(title, options, order)


        card = self.create_card(title=title, description=description, tags=tags)
        card_id = card.get("id")

        # Добавляем id карточки в поле заказа
        if card_id:
            fresh = await Order.get(id=order.id)
            fresh.kaiten_card_id = card_id
            await fresh.save(update_fields=["kaiten_card_id"])

        return card_id
