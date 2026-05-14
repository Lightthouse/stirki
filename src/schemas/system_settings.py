from pydantic import BaseModel


class SystemSettings(BaseModel):
    free_tariff_is_available: bool

    model_config = {"from_attributes": True}
