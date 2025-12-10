# test_db.py
import asyncio
from src.db.database import init_db, close_db
from src.models.models import Client, Order, OrderStatus, Street

async def main():
    await init_db()
    print("Подключились к базе")

    # Найдём статус "new"
    status_new = await OrderStatus.get(name="new")
    street = await Street.first()

    # Создадим тестового клиента
    client, created = await Client.get_or_create(
        telegram_id=777777,
        defaults={
            "phone": "+79991234567",
            "house": "д.7 к.2",
            "street": street,
            "name": "Тест Тестов"
        }
    )
    if created:
        print(f"Создан клиент: {client.name}")

    # Создадим заказ
    order = await Order.create(
        client=client,
        status=status_new,
        street=street,
        house="д.7 к.2",
        total_price_rub=1290,
        need_ironing=True,
        need_conditioner=True,
    )
    print(f"Создан заказ №{order.id} на {order.total_price_rub}₽")

    await close_db()

from src.repositories import repo

async def test_repo():
    await init_db()

    client = await repo.get_or_create_client(
        telegram_id=999999,
        phone="+79990011223",
        name="Иван Иванов",
        street_name="Новорождественская",
        house="д.15 к.3",
        entrance="2",
        floor="5",
        comment="домофон 123"
    )
    print(f"Клиент: {client.name}, заказов: {client.total_orders}")

    order = await repo.create_order(
        client=client,
        street_name="Новорождественская",
        house="д.15 к.3",
        services={"ironing": True, "conditioner": True},
        comment="Срочно!",
        delivery_exact_time=datetime(2025, 12, 15, 18, 0)
    )
    print(f"Создан заказ #{order.id} на {order.total_price_rub}₽")

    await repo.update_status(order, "courier_pickup", changed_by="manager")
    print(f"Статус обновлён → {order.status.name}")

    await close_db()
    
if __name__ == "__main__":
    asyncio.run(test_repo())
