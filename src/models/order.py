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
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("total_price_rub >= 0", name="orders_total_price_check"),
        CheckConstraint(
            "payment_status in ('pending', 'waiting_for_capture', 'succeeded', 'canceled')",
            name="orders_payment_status_check",
        ),
        CheckConstraint(
            "washing_type in ('bag', 'piece')",
            name="orders_washing_type_check",
        ),
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
    bags_number: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    ironing: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    conditioner: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    vacuum_pack: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    stain_remover: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    wash_bag: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    bleach: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    color_catcher_sheets: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )

    total_price_rub: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_status: Mapped[str] = mapped_column(
        Text, default="pending", server_default="pending"
    )
    yookassa_payment_id: Mapped[str | None] = mapped_column(Text)
    yookassa_confirmation_url: Mapped[str | None] = mapped_column(Text)

    kaiten_card_id: Mapped[int | None] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    client: Mapped["Client"] = relationship(back_populates="orders")  # noqa: F821
    status: Mapped["OrderStatus"] = relationship()
    history: Mapped[list["OrderStatusHistory"]] = relationship(back_populates="order")


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
