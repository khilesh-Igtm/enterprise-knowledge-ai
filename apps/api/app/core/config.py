from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Enterprise Knowledge AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    STORAGE_DIR: str = "./storage"
    MAX_UPLOAD_SIZE: int = 20 * 1024 * 1024
    ALLOWED_DOCUMENT_EXTENSIONS: list[str] = [
        ".pdf",
        ".docx",
        ".txt",
    ]

    test_database_url: str | None = None

    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/knowledge_ai"
    )

    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    QDRANT_URL: str = "http://localhost:6333"

    LOG_LEVEL: str = "INFO"

    jwt_secret_key: str = Field(
        default="CHANGE_THIS_TO_A_RANDOM_SECRET_OF_AT_LEAST_32_CHARS",
        min_length=32,
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    jwt_issuer: str = "enterprise-knowledge-ai"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
