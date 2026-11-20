import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from src.database import engine
from src.models.analytics import Ad
from src.settings import AppSettings
from src.api.routers import addresses, auth, services, orders, payments, analytics, texts
from src.api.dependencies import get_db
from src.repositories.system_settings import get_system_settings as load_system_settings
from src.schemas.system_settings import SystemSettings as SystemSettingsSchema
from src.services.ads import ADS_DIR
from src.services.payment_sync import payment_sync_loop
from src.services.schedule import is_accepting_orders
from src.admin import create_admin

# Без этого logger.info/exception из модулей src.* не видны в логах uvicorn.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app_settings = AppSettings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    sync_task = asyncio.create_task(payment_sync_loop())
    yield
    sync_task.cancel()
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
    allow_origins=[f"https://{app_settings.DOMAIN}", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ADS_DIR.mkdir(exist_ok=True)
app.mount("/advertising", StaticFiles(directory=ADS_DIR), name="advertising")

app.include_router(addresses.router, prefix="/api/addresses", tags=["addresses"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(services.router, prefix="/api/services", tags=["services"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(payments.router, prefix="/api/payments", tags=["payments"])
app.include_router(analytics.router, prefix="/api")
app.include_router(texts.router, prefix="/api/texts", tags=["texts"])

create_admin(app)


@app.get("/api/advertising")
async def list_ads(session: AsyncSession = Depends(get_db)):
    """Включённые в админке («Реклама») картинки."""
    result = await session.execute(
        select(Ad.image_path).where(Ad.is_active == True).order_by(Ad.id)  # noqa: E712
    )
    return {"images": list(result.scalars())}


@app.get("/api/system-settings", response_model=SystemSettingsSchema)
async def get_system_settings(session: AsyncSession = Depends(get_db)):
    settings = await load_system_settings(session)
    return SystemSettingsSchema(
        free_tariff_is_available=settings.free_tariff_is_available,
        free_bag_slots=settings.free_bag_slots,
        free_piece_slots=settings.free_piece_slots,
        paid_bag_slots=settings.paid_bag_slots,
        paid_piece_slots=settings.paid_piece_slots,
        order_accept_from=settings.order_accept_from,
        order_accept_to=settings.order_accept_to,
        next_day_delivery_from_hour=settings.next_day_delivery_from_hour,
        free_orders_per_address_per_day=settings.free_orders_per_address_per_day,
        ad_count=settings.ad_count,
        ad_duration_sec=settings.ad_duration_sec,
        support_phone=settings.support_phone,
        support_telegram=settings.support_telegram,
        support_email=settings.support_email,
        promo_enabled=settings.promo_enabled,
        promo_label=settings.promo_label,
        is_accepting_orders=is_accepting_orders(settings),
    )


@app.get("/api/health")
async def health():
    return {"status": "ok"}
