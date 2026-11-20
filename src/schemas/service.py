from pydantic import BaseModel


class ServiceOut(BaseModel):
    slug: str
    name: str
    price_rub: int
    # обычная цена, если сейчас действует акция (сайт её зачёркивает); иначе null
    regular_price_rub: int | None = None
    is_active: bool

    model_config = {"from_attributes": True}
