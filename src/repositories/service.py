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

    async def get_names(self, slugs: list[str]) -> dict[str, str]:
        """slug → название, включая выключенные услуги (они могут быть в старых заказах)."""
        if not slugs:
            return {}
        result = await self.session.execute(select(Service).where(Service.slug.in_(slugs)))
        return {s.slug: s.name for s in result.scalars()}
