# src/models/models.py
from tortoise.models import Model
from tortoise import fields
from typing import Optional

class Street(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=50, unique=True)
    #houses = fields.JSONField(default=list)
    
    class Meta:
        table = "streets"
        
    def __str__(self):
        return self.name

class Client(Model):
    id = fields.BigIntField(pk=True)
    telegram_id = fields.BigIntField(unique=True)
    name = fields.TextField(null=True)
    phone = fields.TextField()
    street = fields.ForeignKeyField("models.Street", related_name="clients", null=True)
    house = fields.TextField()
    entrance = fields.TextField(null=True)
    floor = fields.TextField(null=True)
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
    
    street = fields.ForeignKeyField("models.Street", null=True)
    house = fields.TextField()
    entrance = fields.TextField(null=True)
    floor = fields.TextField(null=True)
    comment = fields.TextField(null=True)

    weight_kg = fields.IntField(default=3)
    need_ironing = fields.BooleanField(default=False)
    need_conditioner = fields.BooleanField(default=False)
    need_vacuum_pack = fields.BooleanField(default=False)
    need_uv = fields.BooleanField(default=False)
    need_wash_bag = fields.BooleanField(default=False)
    delivery_exact_time = fields.DatetimeField(null=True)

    total_price_rub = fields.IntField()
    payment_id = fields.TextField(null=True)
    payment_status = fields.TextField(default="pending")

    trello_card_id = fields.TextField(null=True)

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
