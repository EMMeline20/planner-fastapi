from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения. Значения читаются из .env и переменных окружения."""

    mongodb_url: str = "mongodb://127.0.0.1:27017"
    mongodb_db: str = "tko"
    host: str = "127.0.0.1"
    port: int = 8090

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
