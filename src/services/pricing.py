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
        service_slugs: list[str],
        washing_type: str = "bag",
    ) -> int:
        addon_total = sum(self._price_map.get(slug, 0) for slug in service_slugs)
        if washing_type == "piece":
            piece_price = self._price_map.get("piece", 190)
            return piece_price + addon_total
        return (self.base_price + addon_total) * bags_number

    def service_flags(self, service_slugs: list[str]) -> dict[str, bool]:
        """Convert list of slugs to boolean flags for Order model fields."""
        all_service_fields = [
            "ironing",
            "conditioner",
            "vacuum_pack",
            "stain_remover",
            "wash_bag",
            "bleach",
            "color_catcher_sheets",
        ]
        return {field: field in service_slugs for field in all_service_fields}
