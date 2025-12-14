"""Azure Key Vault integration utilities."""
import os
from typing import Any

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from pydantic.fields import FieldInfo
from pydantic_settings.sources import PydanticBaseSettingsSource


def _snake_to_dash_case(name: str) -> str:
    """Convert snake_case to dash-case (kebab-case)."""
    return name.replace("_", "-").lower()


def _get_key_vault_client(key_vault_uri: str) -> SecretClient | None:
    """Get or create Key Vault client."""
    if not key_vault_uri:
        return None

    credential = DefaultAzureCredential()
    return SecretClient(vault_url=key_vault_uri, credential=credential)


def get_secret_from_key_vault(key_vault_uri: str, secret_name: str) -> str | None:
    """Fetch a secret from Azure Key Vault."""
    if not key_vault_uri:
        return None

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
    """Pydantic settings source for Azure Key Vault.
    
    Converts field names from snake_case to dash-case for Key Vault secret names.
    For example: 'azure_storage_connection_string' -> 'azure-storage-connection-string'
    """

    def __init__(self, settings_cls: type, key_vault_uri: str | None = None):
        """Initialize the Key Vault settings source.
        
        Args:
            settings_cls: The settings class
            key_vault_uri: Optional Key Vault URI. If not provided, reads from AZURE_KEY_VAULT_URI env var.
        """
        super().__init__(settings_cls)
        self.key_vault_uri = key_vault_uri or os.getenv("AZURE_KEY_VAULT_URI")
        self._client: SecretClient | None = None

    def _get_client(self) -> SecretClient | None:
        """Get or create Key Vault client (cached)."""
        if not self.key_vault_uri:
            return None
        if self._client is None:
            self._client = _get_key_vault_client(self.key_vault_uri)
        return self._client

    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        """Get field value from Key Vault.
        
        Args:
            field: The field info
            field_name: The field name
            
        Returns:
            Tuple of (value, key, is_complex) where:
            - value: The secret value or None if not found
            - key: The field name to use
            - is_complex: Whether the value is complex (JSON)
        """
        if not self.key_vault_uri:
            return None, field_name, False

        # Convert field name to dash-case for Key Vault secret name
        secret_name = _snake_to_dash_case(field_name)

        # Try to get secret from Key Vault
        secret_value = get_secret_from_key_vault(self.key_vault_uri, secret_name)

        # Check if field is complex (needs JSON parsing)
        is_complex = self.field_is_complex(field)

        return secret_value, field_name, is_complex

    def __call__(self) -> dict[str, Any]:
        """Load all settings from Key Vault."""
        if not self.key_vault_uri:
            return {}

        data: dict[str, Any] = {}

        # Iterate through all fields in the settings class
        for field_name, field_info in self.settings_cls.model_fields.items():
            value, key, is_complex = self.get_field_value(field_info, field_name)
            if value is not None:
                # Prepare the value (handles complex types)
                prepared_value = self.prepare_field_value(field_name, field_info, value, is_complex)
                data[key] = prepared_value

        return data

