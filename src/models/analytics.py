from datetime import datetime

from sqlalchemy import BigInteger, Integer, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class AdView(Base):
    __tablename__ = "ad_views"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    image_path: Mapped[str] = mapped_column(Text, nullable=False)
    client_id: Mapped[int | None] = mapped_column(BigInteger)
    viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AdViewStats(Base):
    """Read-only view: агрегированная статистика просмотров рекламы."""
    __tablename__ = "ad_view_stats"

    image_path: Mapped[str] = mapped_column(Text, primary_key=True)
    total_views: Mapped[int] = mapped_column(Integer)
    unique_viewers: Mapped[int] = mapped_column(Integer)


class QrCode(Base):
    __tablename__ = "qr_codes"

    code: Mapped[int] = mapped_column(Integer, primary_key=True)
    address_slug: Mapped[str] = mapped_column(Text, nullable=False)
    address_name: Mapped[str] = mapped_column(Text, nullable=False)
    visit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")


class LandingVisit(Base):
    __tablename__ = "landing_visits"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ref_code: Mapped[str] = mapped_column(Text, nullable=False)
    visited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
