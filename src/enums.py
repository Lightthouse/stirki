from enum import StrEnum

class OrderStatusName(StrEnum):
    NEW = "new"
    COURIER_PICKUP = "courier_pickup"
    PICKED_UP = "picked_up"
    WASHING = "washing"
    DRYING = "drying"
    IRONING = "ironing"
    PACKING = "packing"
    COURIER_DELIVERY = "courier_delivery"
    DELIVERED = "delivered"
    CANCELED = "canceled"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    WAITING_FOR_CAPTURE = "waiting_for_capture"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"


class ServiceSlug(StrEnum):
    BASE = "base"
    IRONING = "ironing"
    CONDITIONER = "conditioner"
    VACUUM_PACK = "vacuum_pack"
    EXACT_TIME = "exact_time"
    UV = "uv"
    WASH_BAG = "wash_bag"


class TrelloColumns(StrEnum):
    NEW = "6937fbb94729e78b4259f9ab"
    COURIER_PICKUP = "6937fbbecd4f38c1355942e6"
    PICKED_UP = "693ae340f54ee66d6e8e8590"
    WASHING = "6937fbac2dcd2ca31a7e3f0a"
    DRYING = "693ae31a19f29ad53f5e635a"
    IRONING = "693ae3132e84c05d441a16aa"
    PACKING = "693ae330c43f8bb0a4d5b957"
    COURIER_DELIVERY = "693bf73ab7d5554458197c2d"
    DELIVERED = "6937fbc6b8b81dd552509545"
    CANCELED = "6937fbcfaba20bba23941dd2"


