from enum import StrEnum


class OrderStatusName(StrEnum):
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
