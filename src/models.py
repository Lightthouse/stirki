from tortoise.models import Model
from tortoise import fields
from typing import Optional


class Client(Model):
    id = fields.BigIntField(pk=True)
    telegram_id = fields.BigIntField(unique=True)
    name = fields.TextField(null=True)
    phone = fields.TextField()

    street = fields.TextField()
    house = fields.TextField()
    apartment = fields.IntField()
    entrance = fields.IntField()
    floor = fields.IntField()
    comment = fields.TextField(null=True)

    registered_at = fields.DatetimeField(auto_now_add=True)
    total_orders = fields.IntField(default=0)

    class Meta:
        table = "clients"

class OrderStatus(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=50, unique=True)
    
    class Meta:
        table = "order_statuses"
    
class Order(Model):
    id = fields.BigIntField(pk=True)
    client = fields.ForeignKeyField("models.Client", related_name="orders")
    status = fields.ForeignKeyField("models.OrderStatus", related_name="orders")
    
    street = fields.TextField()
    house = fields.TextField()
    entrance = fields.IntField()
    floor = fields.IntField()
    apartment = fields.IntField()
    comment = fields.TextField(null=True)

    bags_number = fields.IntField(default=1)
    ironing = fields.BooleanField(default=False)
    conditioner = fields.BooleanField(default=False)
    vacuum_pack = fields.BooleanField(default=False)
    stain_remover = fields.BooleanField(default=False)
    wash_bag = fields.BooleanField(default=False)
    bleach = fields.BooleanField(default=False)
    color_catcher_sheets = fields.BooleanField(default=False)


    total_price_rub = fields.IntField()
    payment_id = fields.TextField(null=True)
    payment_status = fields.TextField(default="pending")

    kaiten_card_id = fields.IntField(null=True)
    telegram_chat_id = fields.IntField()
    telegram_message_id = fields.IntField()

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "orders"

class OrderStatusHistory(Model):
    id = fields.BigIntField(pk=True)
    order = fields.ForeignKeyField("models.Order", related_name="history")
    status = fields.ForeignKeyField("models.OrderStatus")
    changed_at = fields.DatetimeField(auto_now_add=True)
    changed_by = fields.TextField(null=True)

    class Meta:
        table = "order_status_history"
