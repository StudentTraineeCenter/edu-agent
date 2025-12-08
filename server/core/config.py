import os
from dataclasses import dataclass
from typing import Optional

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv

load_dotenv()

# Key Vault URI (optional - if set, secrets will be fetched from Key Vault)
_KEY_VAULT_URI = os.getenv("AZURE_KEY_VAULT_URI")

# Cache credential and client to avoid multiple credential attempts
_key_vault_credential: Optional[DefaultAzureCredential] = None
_key_vault_client: Optional[SecretClient] = None


def _get_key_vault_client() -> Optional[SecretClient]:
    """Get or create Key Vault client if URI is configured."""
    global _key_vault_client, _key_vault_credential

    if not _KEY_VAULT_URI:
        return None

    if _key_vault_client is None:
        if _key_vault_credential is None:
            _key_vault_credential = DefaultAzureCredential()
        _key_vault_client = SecretClient(
            vault_url=_KEY_VAULT_URI, credential=_key_vault_credential
        )

    return _key_vault_client


def _get_secret_from_key_vault(key_vault_uri: str, secret_name: str) -> Optional[str]:
    """Fetch a secret from Azure Key Vault."""
    client = _get_key_vault_client()
    if not client:
        return None

    try:
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
            # print(f"{secret_name}={secret_value}")
            return secret_value

    # Fall back to environment variable
    env_value = os.getenv(env_var_name)
    if env_value:
        return env_value

    # Use default if provided
    if default is not None:
        return default

    return "missing_env_var"


@dataclass(frozen=True)
class AppConfig:
    # DATABASE
    DATABASE_URL: str = _get_config_value(
        _KEY_VAULT_URI,
        "database-url",
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres",
    )
    # DATABASE_URL = "postgresql+psycopg2://postgres:HRY-fda*meb4nuk2tky@db.gtyatuwgnpolxjferhju.supabase.co:5432/postgres?sslmode=require"

    # BLOB
    AZURE_STORAGE_CONNECTION_STRING: str = _get_config_value(
        _KEY_VAULT_URI,
        "azure-storage-connection-string",
        "AZURE_STORAGE_CONNECTION_STRING",
    )

    AZURE_STORAGE_INPUT_CONTAINER_NAME: str = _get_config_value(
        _KEY_VAULT_URI,
        "azure-storage-input-container-name",
        "AZURE_STORAGE_INPUT_CONTAINER_NAME",
        "input",
    )

    AZURE_STORAGE_OUTPUT_CONTAINER_NAME: str = _get_config_value(
        _KEY_VAULT_URI,
        "azure-storage-output-container-name",
        "AZURE_STORAGE_OUTPUT_CONTAINER_NAME",
        "output",
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

    # SUPABASE
    SUPABASE_URL: str = _get_config_value(
        _KEY_VAULT_URI,
        "supabase-url",
        "SUPABASE_URL",
    )

    SUPABASE_SERVICE_ROLE_KEY: str = _get_config_value(
        _KEY_VAULT_URI,
        "supabase-service-role-key",
        "SUPABASE_SERVICE_ROLE_KEY",
    )

    SUPABASE_JWT_SECRET: str = _get_config_value(
        _KEY_VAULT_URI,
        "supabase-jwt-secret",
        "SUPABASE_JWT_SECRET",
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

    # CORS
    CORS_ALLOWED_ORIGINS: str = os.getenv("CORS_ALLOWED_ORIGINS", "*")


app_config = AppConfig()
