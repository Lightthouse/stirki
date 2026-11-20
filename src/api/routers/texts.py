from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.models.site_text import SiteText

router = APIRouter()


class SiteTextOut(BaseModel):
    title: str
    body: str


@router.get("/{slug}", response_model=SiteTextOut)
async def get_text(slug: str, session: AsyncSession = Depends(get_db)):
    text = await session.get(SiteText, slug)
    if text is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Текст не найден")
    return SiteTextOut(title=text.title, body=text.body.strip())
