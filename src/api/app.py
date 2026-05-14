from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from src.database import engine
from src.settings import AppSettings
from src.api.routers import addresses, auth, services, orders, payments, analytics
from src.api.dependencies import get_db
from src.models.system_settings import SystemSettings as SystemSettingsModel
from src.schemas.system_settings import SystemSettings as SystemSettingsSchema
from src.admin import create_admin

app_settings = AppSettings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="Стирки ON",
    description="API сервиса доставки стирки",
    version="0.5.0",
    lifespan=lifespan,
)

app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[app_settings.FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/advertising", StaticFiles(directory="advertising"), name="advertising")

app.include_router(addresses.router, prefix="/api/addresses", tags=["addresses"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(services.router, prefix="/api/services", tags=["services"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(payments.router, prefix="/api/payments", tags=["payments"])
app.include_router(analytics.router, prefix="/api")

create_admin(app)


_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
_ADVERTISING_DIR = Path("advertising")


@app.get("/api/advertising")
async def list_ads():
    files = sorted(
        f"/advertising/{p.name}"
        for p in _ADVERTISING_DIR.iterdir()
        if p.suffix.lower() in _IMAGE_EXTENSIONS
    )
    return {"images": files}


@app.get("/api/system-settings", response_model=SystemSettingsSchema)
async def get_system_settings(session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(SystemSettingsModel).limit(1))
    settings = result.scalar_one_or_none()
    if settings is None:
        return SystemSettingsSchema(free_tariff_is_available=True)
    return SystemSettingsSchema.model_validate(settings)



@app.get("/api/health")
async def health():
    return {"status": "ok"}
