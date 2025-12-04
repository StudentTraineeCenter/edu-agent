data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "main" {
  name                = var.key_vault_name
  location            = var.location
  resource_group_name = var.resource_group_name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = var.sku_name

  # Enable RBAC authorization (modern best practice)
  rbac_authorization_enabled = true

  # Network ACLs - allow all networks by default
  network_acls {
    default_action = "Allow"
    bypass         = "AzureServices"
  }

  tags = var.tags
}

# Store secrets in Key Vault
resource "azurerm_key_vault_secret" "database_url" {
  count = var.database_url != null ? 1 : 0

  name         = "database-url"
  value        = var.database_url
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault.main]
}

resource "azurerm_key_vault_secret" "azure_storage_connection_string" {
  count = var.azure_storage_connection_string != null ? 1 : 0

  name         = "azure-storage-connection-string"
  value        = var.azure_storage_connection_string
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault.main]
}

resource "azurerm_key_vault_secret" "azure_storage_input_container_name" {
  count = var.azure_storage_input_container_name != null ? 1 : 0

  name         = "azure-storage-input-container-name"
  value        = var.azure_storage_input_container_name
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault.main]
}

resource "azurerm_key_vault_secret" "azure_storage_output_container_name" {
  count = var.azure_storage_output_container_name != null ? 1 : 0

  name         = "azure-storage-output-container-name"
  value        = var.azure_storage_output_container_name
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault.main]
}

# Note: AI-related secrets are created in main.tf after AI module is created
# This keeps the module focused on basic infrastructure secrets



