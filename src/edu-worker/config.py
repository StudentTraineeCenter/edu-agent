from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from edu_shared.keyvault import KeyVaultSettingsSource


class Settings(BaseSettings):
    """Application settings loaded from Key Vault or environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Azure Storage connection string
    azure_storage_connection_string: str = ""
    azure_storage_queue_name: str = "ai-generation-tasks"
    azure_storage_input_container_name: str = "input"
    azure_storage_output_container_name: str = "output"

    # Azure Content Understanding
    azure_cu_endpoint: str = ""
    azure_cu_key: str = ""
    azure_cu_analyzer_id: str = "prebuilt-documentAnalyzer"

    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_chat_deployment: str = "gpt-4o-mini"
    azure_openai_embedding_deployment: str = "text-embedding-3-large"
    azure_openai_api_version: str = "2024-12-01-preview"

    # Database
    database_url: str = ""

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
            KeyVaultSettingsSource(settings_cls, "https://kv-eduagent-dev-swc-fzgz.vault.azure.net/"),  # Key Vault first (highest priority)
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
