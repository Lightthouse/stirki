import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.enums import KaitenColumns
from src.models.client import Client
from src.models.order import Order
from src.repositories.order import OrderRepository
from src.services.baserow import BaserowService
from src.services.kaiten_kanban import Kaiten

logger = logging.getLogger(__name__)


class OrderService:
    def __init__(self, session: AsyncSession):
        self._repo = OrderRepository(session)

    async def create(
        self,
        client: Client,
        washing_type: str,
        bags_number: int,
        services: dict[str, bool],
        total_price_rub: int,
        status_name: str,
        comment: str | None = None,
    ) -> Order:
        order = await self._repo.create(
            client=client,
            washing_type=washing_type,
            bags_number=bags_number,
            services=services,
            total_price_rub=total_price_rub,
            status_name=status_name,
            comment=comment,
        )
        try:
            with Kaiten() as k:
                card_id = await k.add_card_to_order(order)
            if card_id:
                await self._repo.set_kaiten_card_id(order, card_id)
        except Exception:
            logger.exception("Не удалось создать карточку Kaiten для заказа %s", order.id)

        await BaserowService().sync_order(order, client.phone)

        return order

    async def update_status(
        self,
        order: Order,
        status_name: str,
        payment_status: str | None = None,
        changed_by: str = "system",
        skip_kaiten: bool = False,
    ) -> Order:
        order = await self._repo.update_status(
            order,
            status_name=status_name,
            payment_status=payment_status,
            changed_by=changed_by,
        )
        if not skip_kaiten:
            try:
                if order.kaiten_card_id:
                    column = getattr(KaitenColumns, status_name.upper(), None)
                    if column:
                        with Kaiten() as k:
                            k.change_card_status(order.kaiten_card_id, column)
                        logger.info("Kaiten: карточка %s → %s", order.kaiten_card_id, status_name)
            except Exception:
                logger.exception("Не удалось обновить карточку Kaiten для заказа %s", order.id)

        return order

    async def update_payment(
        self,
        order: Order,
        yookassa_payment_id: str,
        yookassa_confirmation_url: str | None = None,
    ) -> Order:
        return await self._repo.update_payment(
            order,
            yookassa_payment_id=yookassa_payment_id,
            yookassa_confirmation_url=yookassa_confirmation_url,
        )

    async def get_by_id(self, order_id: int) -> Order | None:
        return await self._repo.get_by_id(order_id)

    async def get_by_client_id(self, client_id: int) -> list[Order]:
        return await self._repo.get_by_client_id(client_id)
