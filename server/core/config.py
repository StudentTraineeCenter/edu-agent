import os
from dataclasses import dataclass
from typing import Optional

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv

load_dotenv()


def _get_secret_from_key_vault(key_vault_uri: str, secret_name: str) -> Optional[str]:
    """Fetch a secret from Azure Key Vault."""
    try:
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=key_vault_uri, credential=credential)
        secret = client.get_secret(secret_name)
        return secret.value
    except Exception:
        # If Key Vault access fails, return None to fall back to env vars
        return None


def _get_config_value(
    key_vault_uri: Optional[str],
    secret_name: str,
    env_var_name: str,
    default: Optional[str] = None,
) -> str:
    """Get configuration value from Key Vault or environment variable."""
    # Try Key Vault first if URI is provided
    if key_vault_uri:
        secret_value = _get_secret_from_key_vault(key_vault_uri, secret_name)
        if secret_value:
            return secret_value

    # Fall back to environment variable
    env_value = os.getenv(env_var_name)
    if env_value:
        return env_value

    # Use default if provided
    if default is not None:
        return default

    return "missing_env_var"


# Key Vault URI (optional - if set, secrets will be fetched from Key Vault)
_KEY_VAULT_URI = os.getenv("AZURE_KEY_VAULT_URI")


@dataclass(frozen=True)
class AppConfig:
    # DATABASE
    DATABASE_URL: str = _get_config_value(
        _KEY_VAULT_URI,
        "database-url",
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres",
    )

    # BLOB
    AZURE_STORAGE_CONNECTION_STRING: str = _get_config_value(
        _KEY_VAULT_URI,
        "azure-storage-connection-string",
        "AZURE_STORAGE_CONNECTION_STRING",
    )

    AZURE_STORAGE_CONTAINER_NAME: str = _get_config_value(
        _KEY_VAULT_URI,
        "azure-storage-container-name",
        "AZURE_STORAGE_CONTAINER_NAME",
    )

    # OPENAI
    AZURE_OPENAI_API_KEY: str = _get_config_value(
        _KEY_VAULT_URI,
        "azure-openai-api-key",
        "AZURE_OPENAI_API_KEY",
    )

    AZURE_OPENAI_ENDPOINT: str = _get_config_value(
        _KEY_VAULT_URI,
        "azure-openai-endpoint",
        "AZURE_OPENAI_ENDPOINT",
    )

    AZURE_OPENAI_DEFAULT_MODEL: str = _get_config_value(
        _KEY_VAULT_URI,
        "azure-openai-default-model",
        "AZURE_OPENAI_DEFAULT_MODEL",
        "gpt-4o",
    )

    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = _get_config_value(
        _KEY_VAULT_URI,
        "azure-openai-embedding-deployment",
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
        "text-embedding-3-large",
    )

    AZURE_OPENAI_CHAT_DEPLOYMENT: str = _get_config_value(
        _KEY_VAULT_URI,
        "azure-openai-chat-deployment",
        "AZURE_OPENAI_CHAT_DEPLOYMENT",
        "gpt-4o",
    )

    AZURE_OPENAI_API_VERSION: str = _get_config_value(
        _KEY_VAULT_URI,
        "azure-openai-api-version",
        "AZURE_OPENAI_API_VERSION",
        "2024-06-01",
    )

    # AZURE AI DOCUMENT INTELLIGENCE
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: str = _get_config_value(
        _KEY_VAULT_URI,
        "azure-document-intelligence-endpoint",
        "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT",
    )

    AZURE_DOCUMENT_INTELLIGENCE_KEY: str = _get_config_value(
        _KEY_VAULT_URI,
        "azure-document-intelligence-key",
        "AZURE_DOCUMENT_INTELLIGENCE_KEY",
    )

    # AZURE ENTRA ID
    AZURE_ENTRA_TENANT_ID: str = _get_config_value(
        _KEY_VAULT_URI,
        "azure-entra-tenant-id",
        "AZURE_ENTRA_TENANT_ID",
    )

    AZURE_ENTRA_CLIENT_ID: str = _get_config_value(
        _KEY_VAULT_URI,
        "azure-entra-client-id",
        "AZURE_ENTRA_CLIENT_ID",
    )

    AZURE_CU_ENDPOINT: str = _get_config_value(
        _KEY_VAULT_URI,
        "azure-cu-endpoint",
        "AZURE_CU_ENDPOINT",
    )

    AZURE_CU_KEY: str = _get_config_value(
        _KEY_VAULT_URI,
        "azure-cu-key",
        "AZURE_CU_KEY",
    )

    AZURE_CU_ANALYZER_ID: str = _get_config_value(
        _KEY_VAULT_URI,
        "azure-cu-analyzer-id",
        "AZURE_CU_ANALYZER_ID",
    )

    # USAGE LIMITS (per day per user)
    MAX_CHAT_MESSAGES_PER_DAY: int = int(os.getenv("MAX_CHAT_MESSAGES_PER_DAY", "50"))
    MAX_FLASHCARD_GENERATIONS_PER_DAY: int = int(
        os.getenv("MAX_FLASHCARD_GENERATIONS_PER_DAY", "10")
    )
    MAX_QUIZ_GENERATIONS_PER_DAY: int = int(
        os.getenv("MAX_QUIZ_GENERATIONS_PER_DAY", "10")
    )
    MAX_DOCUMENT_UPLOADS_PER_DAY: int = int(
        os.getenv("MAX_DOCUMENT_UPLOADS_PER_DAY", "5")
    )


app_config = AppConfig()
