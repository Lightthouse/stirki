from pydantic_settings import BaseSettings, SettingsConfigDict


class TelegramSettings(BaseSettings):
    BOT_TOKEN: str
    PAYMENT_PROVIDER_TOKEN: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


tg_settings = TelegramSettings()
