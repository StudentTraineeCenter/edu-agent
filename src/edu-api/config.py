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

    # Azure Storage
    azure_storage_connection_string: str = ""
    azure_storage_queue_name: str = "ai-generation-tasks"
    azure_storage_input_container_name: str = "input"
    azure_storage_output_container_name: str = "output"
    
    # Database
    database_url: str = ""

    # Supabase Auth
    supabase_jwt_secret: str = ""

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
            KeyVaultSettingsSource(settings_cls, "https://kv-eduagent-dev-swc-4xae.vault.azure.net/"),  # Key Vault first (highest priority)
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    res = Settings()
    print(res.model_dump_json(indent=2))
    return res