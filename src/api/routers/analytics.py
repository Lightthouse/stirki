from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.addresses import QR_CODE_MAP
from src.api.dependencies import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])


class TrackVisitIn(BaseModel):
    ref: str


@router.post("/track-visit", status_code=204)
async def track_visit(body: TrackVisitIn, db: AsyncSession = Depends(get_db)):
    try:
        code = int(body.ref)
        ref_code = QR_CODE_MAP.get(code, "invalid")
    except (ValueError, TypeError):
        ref_code = "invalid"

    await db.execute(
        text("INSERT INTO landing_visits (ref_code) VALUES (:ref)"),
        {"ref": ref_code},
    )
    await db.commit()
