from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.repositories.service import ServiceRepository
from src.repositories.system_settings import get_system_settings
from src.schemas.service import ServiceOut
from src.services.pricing import promo_prices

router = APIRouter()


@router.get("", response_model=list[ServiceOut])
async def get_services(session: AsyncSession = Depends(get_db)):
    repo = ServiceRepository(session)
    services = await repo.get_all_active()
    promo = promo_prices(await get_system_settings(session))
    result = []
    for s in services:
        out = ServiceOut.model_validate(s)
        # Сайт считает корзину по price_rub — отдаём цену по акции, обычную — для зачёркивания.
        if s.slug in promo and promo[s.slug] != s.price_rub:
            out.regular_price_rub = s.price_rub
            out.price_rub = promo[s.slug]
        result.append(out)
    return result
