from datetime import date, datetime
from uuid import UUID

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Integer, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class Ad(Base):
    """Рекламная картинка. Показываются только is_active; файл — в advertising/."""
    __tablename__ = "ads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    image_path: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __str__(self) -> str:
        return self.title


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
    # null — картинку удалили из «Рекламы», статистика по ней осталась
    title: Mapped[str | None] = mapped_column(Text)
    total_views: Mapped[int] = mapped_column(Integer)
    unique_viewers: Mapped[int] = mapped_column(Integer)


class LandingVisit(Base):
    __tablename__ = "landing_visits"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    visitor_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    visited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class LandingVisitStats(Base):
    """Read-only view: заходы на главную по дням (МСК)."""
    __tablename__ = "landing_visit_stats"

    day: Mapped[date] = mapped_column(Date, primary_key=True)
    visits: Mapped[int] = mapped_column(Integer)
    unique_visitors: Mapped[int] = mapped_column(Integer)
