# test_db.py
import asyncio
import sys

from src.database import init_db, close_db
from src.devtools import create_test_clients, create_test_orders, delete_test_data, show_summary, delete_all_data


async def main():
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python test_db.py seed      # создать тестовые данные")
        print("  python test_db.py clear     # удалить тестовые данные")
        print("  python test_db.py summary   # показать сводку")
        print("  python test_db.py reset   # удалить всё")
        return

    command = sys.argv[1]


    await init_db()
    try:
        if command == "seed":
            await create_test_clients()
            await create_test_orders()
            await show_summary()
        elif command == "clear":
            await delete_test_data()
            await show_summary()
        elif command == "summary":
            await show_summary()
        elif command == "reset":
            await delete_all_data()
        else:
            print(f"Неизвестная команда: {command}")
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
