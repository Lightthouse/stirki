from pydantic import model_validator
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

    @model_validator(mode="after")
    def _check_production_secrets(self) -> "AppSettings":
        if self.APP_ENV not in ("development", "production"):
            raise ValueError(f"APP_ENV должен быть development или production, а не {self.APP_ENV!r}")
        # В prod без своих секретов админка открылась бы с паролем по умолчанию — не запускаемся.
        if self.APP_ENV == "production":
            weak = [
                name for name in ("SECRET_KEY", "ADMIN_PASSWORD")
                if getattr(self, name) in ("", "change-me-in-production")
            ]
            if weak:
                raise ValueError(f"В production задайте в .env: {', '.join(weak)} (openssl rand -hex 32)")
        return self


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
    # Система налогообложения для чека: osn, usn_income, usn_income_outcome, esn, patent.
    # Пусто — не передаём (поле необязательное).
    TOCHKA_TAX_SYSTEM_CODE: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class SmtpSettings(BaseSettings):
    """Почта для уведомлений операторов о новых заказах.

    Для mail.ru: SMTP_HOST=smtp.mail.ru, SMTP_PORT=465, SMTP_USER — ящик-отправитель,
    SMTP_PASSWORD — «пароль для внешних приложений» (не обычный пароль от ящика).
    """

    SMTP_HOST: str = ""
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    NOTIFY_EMAIL: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
