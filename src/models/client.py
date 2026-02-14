from datetime import datetime

from sqlalchemy import BigInteger, Text, Integer, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    phone: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(Text)

    auth_token: Mapped[str | None] = mapped_column(Text, unique=True)
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    verification_code: Mapped[str | None] = mapped_column(Text)
    verification_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    street: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    house: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    entrance: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    floor: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    apartment: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    comment: Mapped[str | None] = mapped_column(Text)

    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    total_orders: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    orders: Mapped[list["Order"]] = relationship(back_populates="client")  # noqa: F821
