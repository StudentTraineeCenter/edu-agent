from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Azure Storage
    azure_storage_connection_string: str
    azure_storage_queue_name: str = "ai-generation-tasks"

    # Database
    database_url: str


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
