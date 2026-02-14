from pydantic import BaseModel


class ServiceOut(BaseModel):
    slug: str
    name: str
    price_rub: int
    is_active: bool

    model_config = {"from_attributes": True}
