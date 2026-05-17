from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseSettings):
    DB_USER: str = "stirki"
    DB_PASSWORD: str
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "stirki"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"



class AppSettings(BaseSettings):
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_ENV: str = "development"
    DOMAIN: str = "localhost:5173"
    SECRET_KEY: str = "change-me-in-production"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "change-me-in-production"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class SmsAeroSettings(BaseSettings):
    SMSAERO_EMAIL: str = ""
    SMSAERO_API_KEY: str = ""
    SMSAERO_SIGN: str = "SMS"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class TochkaSettings(BaseSettings):
    TOCHKA_TOKEN: str = ""
    TOCHKA_CUSTOMER_CODE_BUISNESS: str = ""
    TOCHKA_CUSTOMER_CODE_PERSONAL: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class BaserowSettings(BaseSettings):
    BASEROW_URL: str = ""
    BASEROW_API_TOKEN: str = ""
    BASEROW_CLIENTS_TABLE_ID: int = 0
    BASEROW_ORDERS_TABLE_ID: int = 0

    @field_validator("BASEROW_CLIENTS_TABLE_ID", "BASEROW_ORDERS_TABLE_ID", mode="before")
    @classmethod
    def empty_str_to_zero(cls, v: object) -> object:
        return 0 if v == "" else v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
