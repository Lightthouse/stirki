import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.client import Client
from src.models.order import Order
from src.repositories.order import OrderRepository
from src.services.baserow import BaserowService

logger = logging.getLogger(__name__)


class OrderService:
    def __init__(self, session: AsyncSession):
        self._repo = OrderRepository(session)

    async def create(
        self,
        client: Client,
        washing_type: str,
        bags_number: int,
        pieces_number: int,
        services: dict[str, bool],
        total_price_rub: int,
        status_name: str,
        comment: str | None = None,
        is_free: bool = False,
    ) -> Order:
        order = await self._repo.create(
            client=client,
            washing_type=washing_type,
            bags_number=bags_number,
            pieces_number=pieces_number,
            services=services,
            total_price_rub=total_price_rub,
            status_name=status_name,
            comment=comment,
            is_free=is_free,
        )

        await BaserowService().sync_order(order, client.phone)

        return order

    async def update_status(
        self,
        order: Order,
        status_name: str,
        payment_status: str | None = None,
        changed_by: str = "system",
    ) -> Order:
        order = await self._repo.update_status(
            order,
            status_name=status_name,
            payment_status=payment_status,
            changed_by=changed_by,
        )

        return order

    async def update_payment(
        self,
        order: Order,
        operation_id: str,
        payment_link: str | None = None,
        payment_token: str | None = None,
    ) -> Order:
        return await self._repo.update_payment(
            order,
            operation_id=operation_id,
            payment_link=payment_link,
            payment_token=payment_token,
        )

    async def get_by_payment_token(self, payment_token: str) -> Order | None:
        return await self._repo.get_by_payment_token(payment_token)

    async def get_by_id(self, order_id: int) -> Order | None:
        return await self._repo.get_by_id(order_id)

    async def get_by_client_id(self, client_id: int) -> list[Order]:
        return await self._repo.get_by_client_id(client_id)
