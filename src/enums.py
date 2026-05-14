from enum import StrEnum

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
    COLOR_CATCHER_SHEETS = 'color_catcher_sheets'

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


