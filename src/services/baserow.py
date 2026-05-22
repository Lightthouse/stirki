import logging

import httpx

from src.models.client import Client
from src.models.order import Order
from src.settings import BaserowSettings

logger = logging.getLogger(__name__)


class BaserowService:
    def __init__(self, settings: BaserowSettings | None = None):
        s = settings or BaserowSettings()
        self._url = s.BASEROW_URL.rstrip("/")
        self._token = s.BASEROW_API_TOKEN
        self._clients_table_id = s.BASEROW_CLIENTS_TABLE_ID
        self._orders_table_id = s.BASEROW_ORDERS_TABLE_ID

    def _is_configured(self) -> bool:
        return bool(self._url and self._token)

    async def sync_client(self, client: Client) -> None:
        """Добавить клиента в таблицу Baserow при первом создании."""
        if not self._is_configured() or not self._clients_table_id:
            return
        payload = {
            "Телефон": client.phone,
            "Зарегистрирован": client.registered_at.isoformat() if client.registered_at else "",
        }
        await self._post_row(self._clients_table_id, payload)

    async def sync_order(self, order: Order, client_phone: str) -> None:
        """Добавить заказ в таблицу Baserow."""
        if not self._is_configured() or not self._orders_table_id:
            return
        services = [name for name, active in {
            "Глажка": order.ironing,
            "Кондиционер": order.conditioner,
            "Вакуумный пакет": order.vacuum_pack,
            "Пятновыводитель": order.stain_remover,
            "Мешок для стирки": order.wash_bag,
            "Отбеливатель": order.bleach,
            "Цветоуловитель": order.color_catcher_sheets,
        }.items() if active]
        payload = {
            "ID заказа": order.id,
            "Телефон клиента": client_phone,
            "Мешков": order.bags_number,
            "Вещей": order.pieces_number,
            "Услуги": ", ".join(services),
            "Сумма (руб)": order.total_price_rub,
            "Статус": order.status.name if order.status else "",
            "Оплата": order.payment_status,
            "Создан": order.created_at.isoformat() if order.created_at else "",
        }
        await self._post_row(self._orders_table_id, payload)

    async def _post_row(self, table_id: int, payload: dict) -> None:
        url = f"{self._url}/api/database/rows/table/{table_id}/?user_field_names=true"
        try:
            async with httpx.AsyncClient(timeout=5.0) as http_client:
                resp = await http_client.post(
                    url,
                    json=payload,
                    headers={"Authorization": f"Token {self._token}"},
                )
                resp.raise_for_status()
        except Exception:
            logger.exception("Не удалось синхронизировать данные с Baserow (table %s)", table_id)
