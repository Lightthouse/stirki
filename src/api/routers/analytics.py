from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.addresses import QR_CODE_MAP
from src.api.dependencies import get_db, get_current_client
from src.models.client import Client

router = APIRouter(prefix="/analytics", tags=["analytics"])


class TrackVisitIn(BaseModel):
    ref: str


class TrackAdViewIn(BaseModel):
    image_path: str


@router.post("/track-ad-view", status_code=204)
async def track_ad_view(
    body: TrackAdViewIn,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        text("INSERT INTO ad_views (image_path, client_id) VALUES (:path, :client_id)"),
        {"path": body.image_path, "client_id": client.id},
    )
    await db.commit()


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
    await db.execute(
        text("UPDATE qr_codes SET visit_count = visit_count + 1 WHERE address_slug = :slug"),
        {"slug": ref_code},
    )
    await db.commit()
