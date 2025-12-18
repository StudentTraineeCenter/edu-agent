from functools import lru_cache

from edu_core.keyvault import KeyVaultSettingsSource
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from Key Vault or environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Azure Storage
    azure_storage_connection_string: str = ""
    azure_storage_queue_name: str = "ai-generation-tasks"
    azure_storage_input_container_name: str = "input"
    azure_storage_output_container_name: str = "output"
    azure_storage_chat_files_container_name: str = "chat-files"

    # Database
    database_url: str = ""

    # Supabase Auth
    supabase_jwt_secret: str = ""

    # Azure OpenAI
    azure_openai_chat_deployment: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = ""
    azure_openai_embedding_deployment: str = ""

    # Usage Limits (per day per user)
    max_chat_messages_per_day: int = 50
    max_flashcard_generations_per_day: int = 10
    max_quiz_generations_per_day: int = 10
    max_document_uploads_per_day: int = 5

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """Customize settings sources to include Key Vault (highest priority)."""
        return (
            KeyVaultSettingsSource(
                settings_cls, "https://kv-eduagent-dev-swc-fzgz.vault.azure.net/"
            ),  # Key Vault first (highest priority)
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
