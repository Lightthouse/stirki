from tortoise import Tortoise
from src.settings import DBSettings

db_settings = DBSettings()


async def init_db() -> None:
    await Tortoise.init(
        db_url=db_settings.DATABASE_URL,
        modules={"models": ["src.models"]},
    )
    # При первом запуске можно раскомментировать, чтобы создать таблицы (но у нас уже есть через init.sql)
    # await Tortoise.generate_schemas()


async def close_db() -> None:
    await Tortoise.close_connections()
