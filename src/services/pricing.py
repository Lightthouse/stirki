from dataclasses import dataclass

from src.models.service import Service
from src.models.system_settings import SystemSettings

# Услуга `<slug>_bag` — цена допуслуги `<slug>` за пакет (отпаривание пакета дороже отпаривания вещи).
# Сама по себе не выбирается; если её нет, за пакет берётся обычная цена допуслуги.
# Ценой за пакет считается только при существующем `<slug>` — иначе это обычный доп, просто с таким окончанием.
BAG_PRICE_SUFFIX = "_bag"


def is_bag_price_slug(slug: str, all_slugs: set[str] | dict) -> bool:
    return slug.endswith(BAG_PRICE_SUFFIX) and slug.removesuffix(BAG_PRICE_SUFFIX) in all_slugs

def promo_prices(settings: SystemSettings) -> dict[str, int]:
    """Цены пакета (`base`) и вещи (`piece`) по акции; пусто — акция выключена, действуют цены из `services`."""
    if not settings.promo_enabled:
        return {}
    return {"base": settings.promo_bag_price, "piece": settings.promo_piece_price}


# Допы, которые нельзя выбрать вместе (на фронтенде — EXCLUSIVE_ADDONS в ServicesCard.tsx).
EXCLUSIVE_ADDONS = [("hypoallergenic_conditioner", "no_conditioner")]


@dataclass(frozen=True)
class OrderLine:
    """Позиция заказа: пакеты или вещи. Она же — позиция кассового чека."""
    name: str
    unit_price: int
    quantity: int

    @property
    def total(self) -> int:
        return self.unit_price * self.quantity


class PricingService:
    def __init__(self, services: list[Service], settings: SystemSettings):
        # Акция подменяет цены пакета и вещи; допы считаются по прайсу как обычно.
        self._price_map: dict[str, int] = {s.slug: s.price_rub for s in services} | promo_prices(settings)
        self._name_map: dict[str, str] = {s.slug: s.name for s in services}
        self.base_price = self._price_map.get("base", 990)
        self.piece_price = self._price_map.get("piece", 190)

    def get_price(self, slug: str) -> int:
        return self._price_map.get(slug, 0)

    def name(self, slug: str) -> str:
        return self._name_map.get(slug, slug)

    def selected_addons(self, service_slugs: list[str]) -> list[str]:
        """Выбранные допы, которые сейчас предлагаются (активны в прайсе); выключенные и цены за пакет отбрасываются."""
        return sorted(
            slug for slug in set(service_slugs)
            if slug in self._price_map and slug not in ("base", "piece")
            and not is_bag_price_slug(slug, self._price_map)
        )

    def order_lines(
        self,
        bags_number: int,
        pieces_number: int,
        service_slugs: list[str],
    ) -> list[OrderLine]:
        """Позиции заказа: пакеты (база + допуслуги за пакет) и вещи (цена вещи + допуслуги).

        Допуслуги выбираются на весь заказ и применяются к каждой позиции:
        к вещи — по цене допуслуги, к пакету — по цене `<slug>_bag`, если она задана.
        """
        addon_slugs = self.selected_addons(service_slugs)
        addon_piece = sum(self._price_map[slug] for slug in addon_slugs)
        addon_bag = sum(
            self._price_map.get(slug + BAG_PRICE_SUFFIX, self._price_map[slug]) for slug in addon_slugs
        )
        piece_price = self.piece_price
        addons = ", ".join(self._name_map[slug].lower() for slug in addon_slugs)
        suffix = f" ({addons})" if addons else ""

        lines = []
        if bags_number > 0:
            lines.append(OrderLine(f"Стирка пакета вещей{suffix}", self.base_price + addon_bag, bags_number))
        if pieces_number > 0:
            lines.append(OrderLine(f"Стирка одной вещи{suffix}", piece_price + addon_piece, pieces_number))
        return lines

    def calculate_order_price(
        self,
        bags_number: int,
        pieces_number: int,
        service_slugs: list[str],
    ) -> int:
        """Цена = база × пакеты + цена вещи × вещи + допуслуги за каждую позицию."""
        return sum(line.total for line in self.order_lines(bags_number, pieces_number, service_slugs))
