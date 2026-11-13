from dataclasses import dataclass

from src.models.service import Service

# Услуга `<slug>_bag` — цена допуслуги `<slug>` за пакет (глажка пакета дороже глажки вещи).
# Сама по себе не выбирается; если её нет, за пакет берётся обычная цена допуслуги.
BAG_PRICE_SUFFIX = "_bag"


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
    def __init__(self, base_price: int, services: list[Service]):
        self.base_price = base_price
        self._price_map: dict[str, int] = {s.slug: s.price_rub for s in services}
        self._name_map: dict[str, str] = {s.slug: s.name for s in services}

    def get_price(self, slug: str) -> int:
        return self._price_map.get(slug, 0)

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
        addon_slugs = sorted(
            slug for slug in set(service_slugs)
            if slug in self._price_map and not slug.endswith(BAG_PRICE_SUFFIX)
        )
        addon_piece = sum(self._price_map[slug] for slug in addon_slugs)
        addon_bag = sum(
            self._price_map.get(slug + BAG_PRICE_SUFFIX, self._price_map[slug]) for slug in addon_slugs
        )
        piece_price = self._price_map.get("piece", 190)
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
