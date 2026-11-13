from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db, get_current_client
from src.models.client import Client

router = APIRouter(prefix="/analytics", tags=["analytics"])


class TrackVisitIn(BaseModel):
    visitor_id: UUID


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
    await db.execute(
        text("INSERT INTO landing_visits (visitor_id) VALUES (:visitor_id)"),
        {"visitor_id": body.visitor_id},
    )
    await db.commit()
