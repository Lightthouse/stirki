from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.service import Service


class ServiceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_active(self) -> list[Service]:
        result = await self.session.execute(
            select(Service).where(Service.is_active == True).order_by(Service.id)  # noqa: E712
        )
        return list(result.scalars().all())

    async def get_by_slugs(self, slugs: list[str]) -> list[Service]:
        result = await self.session.execute(
            select(Service).where(Service.slug.in_(slugs), Service.is_active == True)  # noqa: E712
        )
        return list(result.scalars().all())

    async def get_base_price(self) -> int:
        result = await self.session.execute(
            select(Service).where(Service.slug == "base")
        )
        base = result.scalar_one_or_none()
        return base.price_rub if base else 890
