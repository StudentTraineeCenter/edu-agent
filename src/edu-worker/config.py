from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Azure Storage connection string
    azure_storage_connection_string: str
    azure_storage_queue_name: str = "ai-generation-tasks"

    # Azure OpenAI
    azure_openai_endpoint: str
    azure_openai_chat_deployment: str = "gpt-4o-mini"
    azure_openai_embedding_deployment: str = "text-embedding-3-large"
    azure_openai_api_version: str = "2024-12-01-preview"

    # Database
    database_url: str

@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
