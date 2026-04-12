import logging
from typing import Any

import httpx

from src.addresses import STREETS_SLUG
from src.settings import KaitenSettings
from src.enums import KaitenColumns, KaitenTagsNames

_SLUG_TO_STREET = {slug: name for name, slug in STREETS_SLUG.items()}

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
        super().__init__(
            message or f"Kaiten API error {response.status_code}: {response.text}"
        )


class Kaiten:
    def __init__(
        self,
        timeout: float = 30.0,
    ):
        self.settings = KaitenSettings()

        self.base_url = f"https://{self.settings.DOMAIN}.kaiten.ru/api/latest"
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
            trust_env=False,
        )

    def _raise_for_status(self, response: httpx.Response) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise KaitenAPIError(response) from exc

    def add_tags_to_card(self, card_id: int, tag: KaitenTagsNames):
        response = self.client.post(f"/cards/{card_id}/tags", json={"name": tag})
        self._raise_for_status(response)
        return response.json()

    def change_card_status(
        self,
        card_id: int,
        status: KaitenColumns = KaitenColumns.NEW,
    ):
        response = self.client.patch(f"/cards/{card_id}", json={"column_id": status})
        self._raise_for_status(response)
        return response.json()

    def create_card(
        self,
        title: str,
        description: str = "",
        column_id: int = KaitenColumns.WAITING_FOR_CAPTURE,
        owner_id: int | None = None,
        responsible_id: int | None = None,
        due_date: str | None = None,
        tags: list[dict[str, KaitenTagsNames]] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
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
            payload["due_date_time_present"] = False
        if tags:
            payload["tags"] = tags

        response = self.client.post("/cards", json=payload)
        self._raise_for_status(response)
        return response.json()

    def get_board_columns(self) -> list[dict[str, Any]]:
        response = self.client.get(f"/boards/{self.settings.BOARD}/columns")
        self._raise_for_status(response)
        return response.json()

    def get_card(self, card_id: int) -> dict[str, Any]:
        response = self.client.get(f"/cards/{card_id}")
        self._raise_for_status(response)
        return response.json()

    def get_tags(self) -> list[dict[str, Any]]:
        response = self.client.get("/tags")
        self._raise_for_status(response)
        return response.json()

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "Kaiten":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    @classmethod
    def _maker_descriptions(
        cls,
        title: str,
        options: dict[KaitenTagsNames, bool],
        order,
    ) -> str:
        street = _SLUG_TO_STREET.get(order.street, order.street)
        is_free = order.total_price_rub == 0
        tariff = "бесплатно" if is_free else "платно"
        unit_label = "Вещь" if order.washing_type == "piece" else "Пакет"
        price_per_unit = order.total_price_rub // order.bags_number if order.bags_number else 0

        main = (
            f"{title}\n\n"
            f"**Основная информация**\n"
            f"- Адрес: {street}, дом {order.house}, квартира {order.apartment}, подъезд {order.entrance}, этаж {order.floor}\n"
            f"- Телефон: {order.client.phone}\n"
            f"- Имя: {order.client.name}\n"
            f"- Количество пакетов: {order.bags_number}\n"
            f"- Сумма заказа: {order.total_price_rub} руб\n"
            f"- Тариф: {tariff}\n"
            f"- Комментарий: {order.comment or '—'}\n"
        )

        active_services = [name for name, active in options.items() if active]
        bags_text = ""
        for i in range(1, order.bags_number + 1):
            bags_text += f"\n**{unit_label} {i}**\n"
            bags_text += "- стирка\n"
            for service_name in active_services:
                bags_text += f"- {service_name}\n"
            bags_text += f"- стоимость {price_per_unit} р\n"

        return main + bags_text

    async def add_card_to_order(self, order) -> int:
        options = {
            KaitenTagsNames.IRONING: order.ironing,
            KaitenTagsNames.CONDITIONER: order.conditioner,
            KaitenTagsNames.VACUUM_PACK: order.vacuum_pack,
            KaitenTagsNames.BLEACH: order.bleach,
            KaitenTagsNames.STAIN_REMOVER: order.stain_remover,
            KaitenTagsNames.WASH_BAG: order.wash_bag,
            KaitenTagsNames.COLOR_CATCHER_SHEETS: order.color_catcher_sheets,
        }
        tags = [
            {"name": op_name} for op_name, op_status in options.items() if op_status
        ]
        title = f"Заказ #{order.id}"
        description = self._maker_descriptions(title, options, order)

        card = self.create_card(title=title, description=description, tags=tags)
        card_id = card.get("id")

        if card_id:
            order.kaiten_card_id = card_id

        return card_id
