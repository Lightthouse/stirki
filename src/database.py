from tortoise import Tortoise
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_USER: str = "stirki"
    DB_PASSWORD: str
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "stirki"

    TRELLO_API_KEY : str
    TRELLO_SECRET : str
    TRELLO_TOKEN : str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def DATABASE_URL(self) -> str:
        return f"postgres://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings() # автоматически подхватит .env, если добавишь туда переменные



async def init_db() -> None:
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["src.models"]},
    )
    # При первом запуске можно раскомментировать, чтобы создать таблицы (но у нас уже есть через init.sql)
    # await Tortoise.generate_schemas()


async def close_db() -> None:
    await Tortoise.close_connections()
