from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Job Portal API"
    app_version: str = "0.1.0"
    database_url: str | None = None

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()