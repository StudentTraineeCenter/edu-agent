data "azurerm_client_config" "current" {}

# ACR Pull role assignments
resource "azurerm_role_assignment" "acr_pull_api" {
  scope                = var.acr_id
  role_definition_name = "AcrPull"
  principal_id         = var.api_app_identity_principal_id
}

resource "azurerm_role_assignment" "acr_pull_web" {
  scope                = var.acr_id
  role_definition_name = "AcrPull"
  principal_id         = var.web_app_identity_principal_id
}

# Storage role assignment for API app
resource "azurerm_role_assignment" "api_to_storage_reader" {
  scope                = var.storage_account_id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = var.api_app_identity_principal_id
}

# User role assignments
resource "azurerm_role_assignment" "user_to_openai" {
  scope                = var.openai_account_id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_role_assignment" "user_to_storage" {
  scope                = var.storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

