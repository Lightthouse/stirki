from enum import StrEnum, IntEnum

class OrderStatusName(StrEnum):
    WAITING_FOR_CAPTURE = "waiting_for_capture"
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


class KaitenColumns(StrEnum):
    WAITING_FOR_CAPTURE = "5558704"
    NEW = "5554116"
    COURIER_PICKUP = "5554117"
    PICKED_UP = "5554118"
    WASHING = "5554091"
    DRYING = "5554092"
    IRONING = "5533329"
    PACKING = "5554207"
    COURIER_DELIVERY = "5554093"
    DELIVERED = "5533330"
    CANCELED = "5554094"

class KaitenTagsIds(IntEnum):
    IRONING = 973971
    CONDITIONER = 973972
    VACUUM_PACK = 973973
    EXACT_TIME = 973979
    UV = 973969
    WASH_BAG = 973975

class KaitenTagsNames(StrEnum):
    IRONING = 'глажка'
    CONDITIONER = 'кондиционер'
    VACUUM_PACK = 'вакуумный пакет'
    EXACT_TIME = 'ко времени'
    UV = 'ультрафиолет'
    WASH_BAG = 'мешок'

