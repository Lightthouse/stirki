from pydantic import BaseModel


class SystemSettings(BaseModel):
    free_tariff_is_available: bool
    free_bag_slots: int
    free_piece_slots: int
    paid_bag_slots: int
    paid_piece_slots: int
    order_accept_from_hour: int
    order_accept_to_hour: int
    next_day_delivery_from_hour: int
    free_orders_per_address_per_day: int
    ad_count: int
    ad_duration_sec: int
    support_phone: str
    support_telegram: str
    support_email: str
    # Вычисляется на сервере по МСК: принимаются ли заказы прямо сейчас.
    is_accepting_orders: bool

    model_config = {"from_attributes": True}
