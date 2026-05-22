from sqlalchemy import Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class SystemSettings(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    free_tariff_is_available: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    free_bag_slots: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    free_piece_slots: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    paid_bag_slots: Mapped[int] = mapped_column(Integer, nullable=False, default=5, server_default="5")
    paid_piece_slots: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
