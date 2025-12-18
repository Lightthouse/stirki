# src/devtools.py
from __future__ import annotations

from datetime import datetime
from typing import List

from src.enums import OrderStatusName
from src.models import Street, Client, Order
from src.repositories import Repository

TEST_MARKER = "[TEST]"

TEST_CLIENTS = [
    {
        "telegram_id": 100001,
        "name": "Иван Петров",
        "phone": "+79990000001",
        "street_name": "Новорождественская",
        "house": "7к1",
        "entrance": "2",
        "floor": "5",
        "apartment": 228,
        "comment": f"{TEST_MARKER} Первый тестовый клиент",
    },
    {
        "telegram_id": 100002,
        "name": "Анна Смирнова",
        "phone": "+79990000002",
        "street_name": "Мытищинская",
        "house": "12",
        "entrance": "1",
        "floor": "3",
        "apartment": 322,
        "comment": f"{TEST_MARKER} Второй тестовый клиент",
    },
    {
        "telegram_id": 100003,
        "name": "Сергей Тест",
        "phone": "+79990000003",
        "street_name": "Новорождественская",
        "house": "9",
        "entrance": None,
        "floor": None,
        "apartment": 2,
        "comment": f"{TEST_MARKER} Третий тестовый клиент",
    },
]

TEST_ORDERS = [
    # базовый заказ без опций
    {
        "need_ironing": False,
        "need_conditioner": False,
        "need_vacuum_pack": False,
        "need_uv": False,
        "need_wash_bag": False,
        "delivery_exact_time": None,
        "comment": f"{TEST_MARKER} Заказ без доп. опций",
    },
    # заказ с глажкой и кондиционером
    {
        "need_ironing": True,
        "need_conditioner": True,
        "need_vacuum_pack": False,
        "need_uv": False,
        "need_wash_bag": False,
        "delivery_exact_time": None,
        "comment": f"{TEST_MARKER} Стирка + глажка + кондиционер",
    },
    # заказ с доставкой ко времени и мешком
    {
        "need_ironing": False,
        "need_conditioner": False,
        "need_vacuum_pack": False,
        "need_uv": False,
        "need_wash_bag": True,
        "delivery_exact_time": datetime(2025, 12, 15, 18, 0),
        "comment": f"{TEST_MARKER} Доставка ко времени + мешок",
    },
]


async def create_test_clients() -> List[Client]:
    clients: List[Client] = []

    for data in TEST_CLIENTS:

        street = await Street.get(name=data["street_name"])
        del data["street_name"]

        client = await Repository.create_client(**data, street=street)
        clients.append(client)

    print(f"Создано/найдено тестовых клиентов: {len(clients)}")
    return clients


async def create_test_orders() -> List[Order]:
    orders: List[Order] = []

    for ind, data in enumerate(TEST_ORDERS):

        client = await Client.get(telegram_id=TEST_CLIENTS[ind]["telegram_id"])

        order = await Repository.create_order(**data, client=client)

        orders.append(order)

    print(f"Создано тестовых заказов: {len(orders)}")
    return orders


async def delete_test_data() -> None:
    # сначала заказы, потом клиенты
    deleted_orders = await Order.filter(comment__contains=TEST_MARKER).delete()
    deleted_clients = await Client.filter(comment__startswith=TEST_MARKER).delete()

    print(f"Удалено тестовых заказов: {deleted_orders}")
    print(f"Удалено тестовых клиентов: {deleted_clients}")


async def show_summary() -> None:
    total_clients = await Client.all().count()
    total_orders = await Order.all().count()

    test_clients = await Client.filter(comment__startswith=TEST_MARKER).count()
    test_orders = await Order.filter(comment__contains=TEST_MARKER).count()

    print("=== Сводка по данным ===")
    print(f"Всего клиентов: {total_clients} (тестовых: {test_clients})")
    print(f"Всего заказов:  {total_orders} (тестовых: {test_orders})")
