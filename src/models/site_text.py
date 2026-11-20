from datetime import datetime

from sqlalchemy import DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class SiteText(Base):
    """Текст окна сайта (оферта, «Подробнее о сервисе», политика ПДн) — правится в админке «Тексты сайта»."""
    __tablename__ = "site_texts"

    slug: Mapped[str] = mapped_column(Text, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    body: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def __str__(self) -> str:
        return SITE_TEXT_NAMES.get(self.slug, self.slug)


# Названия в админке; slug-и — те, что запрашивает сайт (frontend/src/components/ui/*Modal.tsx).
SITE_TEXT_NAMES = {
    "offer": "Публичная оферта",
    "about": "Подробнее о сервисе",
    "privacy": "Политика конфиденциальности",
}
