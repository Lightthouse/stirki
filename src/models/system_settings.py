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

    # Приём заказов по МСК: с from (включительно) до to (не включительно), целые часы.
    order_accept_from_hour: Mapped[int] = mapped_column(Integer, nullable=False, default=9, server_default="9")
    order_accept_to_hour: Mapped[int] = mapped_column(Integer, nullable=False, default=22, server_default="22")
    free_orders_per_address_per_day: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )

    ad_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    ad_duration_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
