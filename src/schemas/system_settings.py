from pydantic import BaseModel


class SystemSettings(BaseModel):
    free_tariff_is_available: bool
    free_bag_slots: int
    free_piece_slots: int
    paid_bag_slots: int
    paid_piece_slots: int

    model_config = {"from_attributes": True}
