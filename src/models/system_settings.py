from sqlalchemy import Integer, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base

# Совпадает с дефолтом в pg_init/01-schema.sql.
DEFAULT_DEBUG_PHONES = "+7 999 999-99-99, +7 888 888-88-88"


class SystemSettings(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    free_tariff_is_available: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    # Вход по SMS. Выключено — SMS не шлются, код возвращается в ответе API и показывается на странице.
    sms_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    # Отладочные номера (src/services/auth.py, is_debug_phone): код на странице, без SMS.
    # Действуют только при включённом флаге — по умолчанию выключен.
    debug_phones_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    debug_phones: Mapped[str] = mapped_column(
        Text, nullable=False, default=DEFAULT_DEBUG_PHONES, server_default=DEFAULT_DEBUG_PHONES
    )
    free_bag_slots: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    free_piece_slots: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    paid_bag_slots: Mapped[int] = mapped_column(Integer, nullable=False, default=5, server_default="5")
    paid_piece_slots: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    # Приём заказов по МСК: с from (включительно) до to (не включительно), целые часы.
    order_accept_from_hour: Mapped[int] = mapped_column(Integer, nullable=False, default=9, server_default="9")
    order_accept_to_hour: Mapped[int] = mapped_column(Integer, nullable=False, default=21, server_default="21")
    # С этого часа (МСК) заказ забирают сразу, а возвращают на следующий день.
    next_day_delivery_from_hour: Mapped[int] = mapped_column(Integer, nullable=False, default=19, server_default="19")
    free_orders_per_address_per_day: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )

    ad_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    ad_duration_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    # Контакты поддержки на сайте. Пустая строка — контакт не показывается.
    support_phone: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    # Имя пользователя Telegram без @ (ссылка https://t.me/<имя>).
    support_telegram: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    support_email: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
