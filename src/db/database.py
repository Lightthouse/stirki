# src/db/database.py
from tortoise import Tortoise
from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    DB_USER: str = "stirki"
    DB_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "test_password")  
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "stirki"
    @property
    def DATABASE_URL(self) -> str:
        return f"postgres://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()  # автоматически подхватит .env, если добавишь туда переменные

async def init_db() -> None:
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["src.models.models"]},
    )
    # При первом запуске можно раскомментировать, чтобы создать таблицы (но у нас уже есть через init.sql)
    # await Tortoise.generate_schemas()

async def close_db() -> None:
    await Tortoise.close_connections()
