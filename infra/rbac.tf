# Role-based access control for managed identities

# Enable system-assigned managed identity for existing storage account
resource "azurerm_storage_account" "main" {
  name                     = "${replace(var.project_name, "-", "")}${var.environment}${random_string.suffix.result}sa"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"

  # Enable system-assigned managed identity
  identity {
    type = "SystemAssigned"
  }

  tags = local.common_tags
}


# Grant current user access to OpenAI (for local development)
data "azurerm_client_config" "current" {}

resource "azurerm_role_assignment" "user_to_openai" {
  scope                = azurerm_cognitive_account.openai.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = data.azurerm_client_config.current.object_id
}


# Grant current user access to storage account
resource "azurerm_role_assignment" "user_to_storage" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}
