from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "AI Job Portal API"
    app_version: str = "0.1.0"
    database_url: str | None = None
    upload_directory: str = "uploads/resumes"
    max_resume_size: int = 5 * 1024 * 1024
    allowed_resume_extensions: str = ".pdf,.docx"
    llm_api_key: str | None = None
    llm_provider: str = "fallback"


    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
