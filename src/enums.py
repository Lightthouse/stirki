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
    IRONING = "ironing"
    CONDITIONER = "conditioner"
    VACUUM_PACK = "vacuum_pack"
    STAIN_REMOVER = "stain_remover"
    WASH_BAG = "wash_bag"
    BLEACH = "bleach"
    COLOR_CATCHER_SHEETS = 'Color_catcher_sheets '

class ServiceCyrillic(StrEnum):
    IRONING = "Глажка"
    CONDITIONER = "Кондиционер"
    VACUUM_PACK = "Вакуумный пакет"
    STAIN_REMOVER = "Пятновыводитель"
    WASH_BAG = "Мешок для стирки"
    BLEACH = "Отбеливатель"
    COLOR_CATCHER_SHEETS = "Салфетки против окрашивания"

ServiceCyrillicSlugMap: dict[ServiceCyrillic, ServiceSlug] = {
    ServiceCyrillic.IRONING: ServiceSlug.IRONING,
    ServiceCyrillic.CONDITIONER: ServiceSlug.CONDITIONER,
    ServiceCyrillic.VACUUM_PACK: ServiceSlug.VACUUM_PACK,
    ServiceCyrillic.STAIN_REMOVER: ServiceSlug.STAIN_REMOVER,
    ServiceCyrillic.WASH_BAG: ServiceSlug.WASH_BAG,
    ServiceCyrillic.BLEACH: ServiceSlug.BLEACH,
    ServiceCyrillic.COLOR_CATCHER_SHEETS: ServiceSlug.COLOR_CATCHER_SHEETS,
}


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
    BLEACH = 973979
    STAIN_REMOVER = 973969
    WASH_BAG = 973975
    COLOR_CATCHER_SHEETS = 1003744

class KaitenTagsNames(StrEnum):
    IRONING = 'глажка'
    CONDITIONER = 'кондиционер'
    VACUUM_PACK = 'вакуумный пакет'
    BLEACH = 'отбеливатель'
    STAIN_REMOVER = 'пятновыводитель'
    WASH_BAG = 'мешок'
    COLOR_CATCHER_SHEETS = 'салфетки'

