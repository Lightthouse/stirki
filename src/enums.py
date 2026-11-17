from enum import StrEnum


class OrderStatusName(StrEnum):
    WAITING_PAYMENT = "waiting_payment"
    COURIER_PICKUP = "courier_pickup"
    PICKED_UP = "picked_up"
    WASHING = "washing"
    COURIER_DELIVERY = "courier_delivery"
    DELIVERED = "delivered"
    CANCELED = "canceled"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"


class Handover(StrEnum):
    """Как курьер забирает и возвращает вещи — клиент выбирает в корзине."""
    DOOR = "door"  # забрать и оставить у двери
    HAND = "hand"  # лично в руки

    @property
    def label(self) -> str:
        return HANDOVER_LABELS[self]


HANDOVER_LABELS = {Handover.DOOR: "Забрать и оставить у двери", Handover.HAND: "Лично в руки"}
