from src.models.service import Service


class PricingService:
    def __init__(self, base_price: int, services: list[Service]):
        self.base_price = base_price
        self._price_map: dict[str, int] = {s.slug: s.price_rub for s in services}

    def get_price(self, slug: str) -> int:
        return self._price_map.get(slug, 0)

    def calculate_order_price(
        self,
        bags_number: int,
        pieces_number: int,
        service_slugs: list[str],
    ) -> int:
        addon_total = sum(self._price_map.get(slug, 0) for slug in service_slugs)
        piece_price = self._price_map.get("piece", 390)
        return self.base_price * bags_number + piece_price * pieces_number + addon_total

