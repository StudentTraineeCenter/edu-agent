import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

# Load .env file early so Key Vault URI is available
env_file = Path(__file__).parent.parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Cache credential and client to avoid multiple credential attempts
_key_vault_credential: Optional[DefaultAzureCredential] = None
_key_vault_client: Optional[SecretClient] = None
_key_vault_uri_cached: Optional[str] = None

# Mapping of field names to their Key Vault secret names
_KEY_VAULT_SECRET_MAP = {
    "DATABASE_URL": "database-url",
    "AZURE_STORAGE_CONNECTION_STRING": "azure-storage-connection-string",
    "AZURE_STORAGE_INPUT_CONTAINER_NAME": "azure-storage-input-container-name",
    "AZURE_STORAGE_OUTPUT_CONTAINER_NAME": "azure-storage-output-container-name",
    "AZURE_OPENAI_API_KEY": "azure-openai-api-key",
    "AZURE_OPENAI_ENDPOINT": "azure-openai-endpoint",
    "AZURE_OPENAI_DEFAULT_MODEL": "azure-openai-default-model",
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "azure-openai-embedding-deployment",
    "AZURE_OPENAI_CHAT_DEPLOYMENT": "azure-openai-chat-deployment",
    "AZURE_OPENAI_API_VERSION": "azure-openai-api-version",
    "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT": "azure-document-intelligence-endpoint",
    "AZURE_DOCUMENT_INTELLIGENCE_KEY": "azure-document-intelligence-key",
    "AZURE_ENTRA_TENANT_ID": "azure-entra-tenant-id",
    "AZURE_ENTRA_CLIENT_ID": "azure-entra-client-id",
    "SUPABASE_URL": "supabase-url",
    "SUPABASE_SERVICE_ROLE_KEY": "supabase-service-role-key",
    "SUPABASE_JWT_SECRET": "supabase-jwt-secret",
    "AZURE_CU_ENDPOINT": "azure-cu-endpoint",
    "AZURE_CU_KEY": "azure-cu-key",
    "AZURE_CU_ANALYZER_ID": "azure-cu-analyzer-id",
}


def _get_key_vault_client(key_vault_uri: Optional[str]) -> Optional[SecretClient]:
    """Get or create Key Vault client if URI is configured."""
    global _key_vault_client, _key_vault_credential, _key_vault_uri_cached

    if not key_vault_uri:
        return None

    # Recreate client if URI changed
    if _key_vault_client is None or _key_vault_uri_cached != key_vault_uri:
        if _key_vault_credential is None:
            _key_vault_credential = DefaultAzureCredential()
        _key_vault_client = SecretClient(
            vault_url=key_vault_uri, credential=_key_vault_credential
        )
        _key_vault_uri_cached = key_vault_uri

    return _key_vault_client


def _get_secret_from_key_vault(
    key_vault_uri: Optional[str], secret_name: str
) -> Optional[str]:
    """Fetch a secret from Azure Key Vault."""
    client = _get_key_vault_client(key_vault_uri)
    if not client:
        return None

    try:
        secret = client.get_secret(secret_name)
        return secret.value
    except Exception:
        # If Key Vault access fails, return None to fall back to env vars
        return None


class KeyVaultSettingsSource(PydanticBaseSettingsSource):
    """Custom settings source that checks Azure Key Vault first."""

    def get_field_value(
        self, field: Any, field_name: str
    ) -> tuple[Any, str | None]:
        """Get field value from Key Vault if available."""
        if field_name not in _KEY_VAULT_SECRET_MAP:
            return None, None

        key_vault_uri = os.getenv("AZURE_KEY_VAULT_URI")
        if not key_vault_uri:
            return None, None

        secret_name = _KEY_VAULT_SECRET_MAP[field_name]
        secret_value = _get_secret_from_key_vault(key_vault_uri, secret_name)
        if secret_value:
            return secret_value, None

        return None, None

    def __call__(self) -> dict[str, Any]:
        """Return settings from Key Vault."""
        key_vault_uri = os.getenv("AZURE_KEY_VAULT_URI")
        if not key_vault_uri:
            return {}

        settings = {}
        for field_name, secret_name in _KEY_VAULT_SECRET_MAP.items():
            secret_value = _get_secret_from_key_vault(key_vault_uri, secret_name)
            if secret_value:
                settings[field_name] = secret_value

        return settings


class Settings(BaseSettings):
    """Application settings loaded from environment variables and Azure Key Vault."""

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Key Vault URI (optional - if set, secrets will be fetched from Key Vault)
    AZURE_KEY_VAULT_URI: Optional[str] = None

    # DATABASE
    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"
    )

    # BLOB
    AZURE_STORAGE_CONNECTION_STRING: str = "missing_env_var"

    AZURE_STORAGE_INPUT_CONTAINER_NAME: str = "input"

    AZURE_STORAGE_OUTPUT_CONTAINER_NAME: str = "output"

    # OPENAI
    AZURE_OPENAI_API_KEY: str = "missing_env_var"

    AZURE_OPENAI_ENDPOINT: str = "missing_env_var"

    AZURE_OPENAI_DEFAULT_MODEL: str = "gpt-4o"

    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = "text-embedding-3-large"

    AZURE_OPENAI_CHAT_DEPLOYMENT: str = "gpt-4o"

    AZURE_OPENAI_API_VERSION: str = "2024-06-01"

    # AZURE ENTRA ID
    AZURE_ENTRA_TENANT_ID: str = "missing_env_var"

    AZURE_ENTRA_CLIENT_ID: str = "missing_env_var"

    # SUPABASE
    SUPABASE_URL: str = "missing_env_var"

    SUPABASE_SERVICE_ROLE_KEY: str = "missing_env_var"

    SUPABASE_JWT_SECRET: str = "missing_env_var"

    AZURE_CU_ENDPOINT: str = "missing_env_var"

    AZURE_CU_KEY: str = "missing_env_var"

    AZURE_CU_ANALYZER_ID: str = "missing_env_var"

    # USAGE LIMITS (per day per user)
    MAX_CHAT_MESSAGES_PER_DAY: int = 50

    MAX_FLASHCARD_GENERATIONS_PER_DAY: int = 10

    MAX_QUIZ_GENERATIONS_PER_DAY: int = 10

    MAX_DOCUMENT_UPLOADS_PER_DAY: int = 5

    # CORS
    CORS_ALLOWED_ORIGINS: str = "*"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customize settings sources: Key Vault first, then .env, then env vars."""
        # Key Vault is checked first, then .env overrides if present, then env vars
        return (
            KeyVaultSettingsSource(settings_cls),  # Key Vault first (fallback)
            dotenv_settings,  # .env file (overrides Key Vault)
            env_settings,  # Environment variables (overrides .env)
            init_settings,  # Defaults (if nothing else set)
            file_secret_settings,
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# For backward compatibility
app_config = get_settings()
