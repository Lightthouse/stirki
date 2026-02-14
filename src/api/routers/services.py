from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.repositories.service import ServiceRepository
from src.schemas.service import ServiceOut

router = APIRouter()


@router.get("", response_model=list[ServiceOut])
async def get_services(session: AsyncSession = Depends(get_db)):
    repo = ServiceRepository(session)
    services = await repo.get_all_active()
    return [ServiceOut.model_validate(s) for s in services]
