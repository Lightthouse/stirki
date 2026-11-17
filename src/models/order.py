from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Integer,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class OrderStatus(Base):
    __tablename__ = "order_statuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)  # Кириллица, для отображения
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)  # Латиница, для кода

    def __str__(self) -> str:
        return self.name


_SERVICE_FIELDS = [
    "ironing",
    "conditioner",
    "vacuum_pack",
    "stain_remover",
    "wash_bag",
    "bleach",
    "color_catcher_sheets",
]


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("total_price_rub >= 0", name="orders_total_price_check"),
        CheckConstraint(
            "payment_status in ('pending', 'succeeded', 'canceled')",
            name="orders_payment_status_check",
        ),
        CheckConstraint("washing_type in ('bag', 'piece', 'mixed')", name="orders_washing_type_check"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    client_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("clients.id"), nullable=False
    )
    status_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("order_statuses.id"), nullable=False
    )

    street: Mapped[str] = mapped_column(Text, nullable=False)
    house: Mapped[str] = mapped_column(Text, nullable=False)
    entrance: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    floor: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    apartment: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)

    washing_type: Mapped[str] = mapped_column(Text, nullable=False, server_default="bag")
    bags_number: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    pieces_number: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    ironing: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    conditioner: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    vacuum_pack: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    stain_remover: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    wash_bag: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    bleach: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    color_catcher_sheets: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    is_free: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    # Оформлен после system_settings.next_day_delivery_from_hour: вещи вернут на следующий день.
    next_day_delivery: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    # Передача вещей: src.enums.Handover (door — у двери, hand — лично в руки).
    handover: Mapped[str] = mapped_column(Text, nullable=False, default="door", server_default="door")
    total_price_rub: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_status: Mapped[str] = mapped_column(
        Text, default="pending", server_default="pending"
    )
    payment_token: Mapped[str | None] = mapped_column(Text, unique=True)
    payment_link_id: Mapped[str | None] = mapped_column(Text)
    operation_id: Mapped[str | None] = mapped_column(Text)
    payment_link: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    client: Mapped["Client"] = relationship(back_populates="orders")  # noqa: F821
    status: Mapped["OrderStatus"] = relationship()
    # История удаляется вместе с заказом. passive_deletes — удаление делает сама БД
    # (on delete cascade в схеме), иначе SQLAlchemy пытается обнулить order_id в истории.
    history: Mapped[list["OrderStatusHistory"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", passive_deletes=True
    )

    @property
    def number(self) -> str:
        """Номер заказа для людей: на сайте, в письмах, в админке, в платеже Точки."""
        return f"ST-{self.id}"

    @property
    def service_slugs(self) -> list[str]:
        """Список активных slug-ов услуг из булевых флагов."""
        return [f for f in _SERVICE_FIELDS if getattr(self, f)]

    @classmethod
    def flags_from_slugs(cls, slugs: list[str]) -> dict[str, bool]:
        """Булевые флаги для полей модели из списка slug-ов."""
        return {f: f in slugs for f in _SERVICE_FIELDS}


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    status_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("order_statuses.id"), nullable=False
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    changed_by: Mapped[str | None] = mapped_column(Text)

    order: Mapped["Order"] = relationship(back_populates="history")
    status: Mapped["OrderStatus"] = relationship()
