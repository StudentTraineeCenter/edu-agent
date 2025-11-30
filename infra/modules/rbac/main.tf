data "azurerm_client_config" "current" {}

# ============================================================================
# Key Vault RBAC Assignments
# ============================================================================

# Server app: Key Vault Secrets User (read secrets)
resource "azurerm_role_assignment" "server_app_key_vault_secrets_user" {
  scope                = var.key_vault_id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = var.server_app_identity_principal_id
}

# Current user: Key Vault Secrets Officer (full secret management for Terraform)
resource "azurerm_role_assignment" "current_user_key_vault_secrets_officer" {
  scope                = var.key_vault_id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}

# ============================================================================
# Azure Container Registry RBAC Assignments
# ============================================================================

# Server app: ACR Pull
resource "azurerm_role_assignment" "server_app_acr_pull" {
  scope                = var.acr_id
  role_definition_name = "AcrPull"
  principal_id         = var.server_app_identity_principal_id
}

# Web app: ACR Pull
resource "azurerm_role_assignment" "web_app_acr_pull" {
  scope                = var.acr_id
  role_definition_name = "AcrPull"
  principal_id         = var.web_app_identity_principal_id
}

# ============================================================================
# Storage Account RBAC Assignments
# ============================================================================

# Server app: Storage Blob Data Contributor (read/write access)
resource "azurerm_role_assignment" "server_app_storage_blob_data_contributor" {
  scope                = var.storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = var.server_app_identity_principal_id
}

# Current user: Storage Blob Data Contributor (for Terraform/debugging)
resource "azurerm_role_assignment" "current_user_storage_blob_data_contributor" {
  scope                = var.storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

# ============================================================================
# AI Foundry (Cognitive Services) RBAC Assignments
# ============================================================================

# Current user: Cognitive Services Contributor (required for managing AI resources)
resource "azurerm_role_assignment" "current_user_cognitive_services_contributor" {
  scope                = var.ai_foundry_cognitive_account_id
  role_definition_name = "Cognitive Services Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Current user: Cognitive Services OpenAI Contributor (required for OpenAI deployments)
resource "azurerm_role_assignment" "current_user_cognitive_services_openai_contributor" {
  scope                = var.ai_foundry_cognitive_account_id
  role_definition_name = "Cognitive Services OpenAI Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

