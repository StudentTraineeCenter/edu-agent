data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "main" {
  name                = var.key_vault_name
  location            = var.location
  resource_group_name = var.resource_group_name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = var.sku_name

  # Enable access policies (for backward compatibility)
  rbac_authorization_enabled = false

  # Network ACLs - allow all networks by default
  network_acls {
    default_action = "Allow"
    bypass         = "AzureServices"
  }

  tags = var.tags
}

# Note: Server app access policy is created in main.tf after app_service is created

# Access policy for current user (for Terraform to write secrets)
resource "azurerm_key_vault_access_policy" "current_user" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id

  secret_permissions = [
    "Get",
    "List",
    "Set",
    "Delete",
    "Recover",
    "Backup",
    "Restore",
  ]
}

# Store secrets in Key Vault
resource "azurerm_key_vault_secret" "database_url" {
  count = var.database_url != null ? 1 : 0

  name         = "database-url"
  value        = var.database_url
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]
}

resource "azurerm_key_vault_secret" "azure_storage_connection_string" {
  count = var.azure_storage_connection_string != null ? 1 : 0

  name         = "azure-storage-connection-string"
  value        = var.azure_storage_connection_string
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]
}

resource "azurerm_key_vault_secret" "azure_storage_container_name" {
  count = var.azure_storage_container_name != null ? 1 : 0

  name         = "azure-storage-container-name"
  value        = var.azure_storage_container_name
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]
}

resource "azurerm_key_vault_secret" "azure_openai_api_key" {
  count = var.azure_openai_api_key != null ? 1 : 0

  name         = "azure-openai-api-key"
  value        = var.azure_openai_api_key
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]
}

resource "azurerm_key_vault_secret" "azure_openai_endpoint" {
  count = var.azure_openai_endpoint != null ? 1 : 0

  name         = "azure-openai-endpoint"
  value        = var.azure_openai_endpoint
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]
}

resource "azurerm_key_vault_secret" "azure_openai_default_model" {
  count = var.azure_openai_default_model != null ? 1 : 0

  name         = "azure-openai-default-model"
  value        = var.azure_openai_default_model
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]
}

resource "azurerm_key_vault_secret" "azure_openai_embedding_deployment" {
  count = var.azure_openai_embedding_deployment != null ? 1 : 0

  name         = "azure-openai-embedding-deployment"
  value        = var.azure_openai_embedding_deployment
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]
}

resource "azurerm_key_vault_secret" "azure_openai_chat_deployment" {
  count = var.azure_openai_chat_deployment != null ? 1 : 0

  name         = "azure-openai-chat-deployment"
  value        = var.azure_openai_chat_deployment
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]
}

resource "azurerm_key_vault_secret" "azure_openai_api_version" {
  count = var.azure_openai_api_version != null ? 1 : 0

  name         = "azure-openai-api-version"
  value        = var.azure_openai_api_version
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]
}

resource "azurerm_key_vault_secret" "azure_document_intelligence_endpoint" {
  count = var.azure_document_intelligence_endpoint != null ? 1 : 0

  name         = "azure-document-intelligence-endpoint"
  value        = var.azure_document_intelligence_endpoint
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]
}

resource "azurerm_key_vault_secret" "azure_document_intelligence_key" {
  count = var.azure_document_intelligence_key != null ? 1 : 0

  name         = "azure-document-intelligence-key"
  value        = var.azure_document_intelligence_key
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]
}

resource "azurerm_key_vault_secret" "azure_entra_tenant_id" {
  count = var.azure_entra_tenant_id != null ? 1 : 0

  name         = "azure-entra-tenant-id"
  value        = var.azure_entra_tenant_id
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]
}

resource "azurerm_key_vault_secret" "azure_entra_client_id" {
  count = var.azure_entra_client_id != null ? 1 : 0

  name         = "azure-entra-client-id"
  value        = var.azure_entra_client_id
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]
}

resource "azurerm_key_vault_secret" "azure_cu_endpoint" {
  count = var.azure_cu_endpoint != null ? 1 : 0

  name         = "azure-cu-endpoint"
  value        = var.azure_cu_endpoint
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]
}

resource "azurerm_key_vault_secret" "azure_cu_key" {
  count = var.azure_cu_key != null ? 1 : 0

  name         = "azure-cu-key"
  value        = var.azure_cu_key
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]
}

resource "azurerm_key_vault_secret" "azure_cu_analyzer_id" {
  count = var.azure_cu_analyzer_id != null ? 1 : 0

  name         = "azure-cu-analyzer-id"
  value        = var.azure_cu_analyzer_id
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]
}

