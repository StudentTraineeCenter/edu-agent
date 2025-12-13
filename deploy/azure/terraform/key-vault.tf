# ============================================================================
# Key Vault
# ============================================================================
resource "azurerm_key_vault" "main" {
  name                = local.key_vault_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  # Enable RBAC authorization (modern best practice)
  rbac_authorization_enabled = true

  # Network ACLs - allow all networks by default
  network_acls {
    default_action = "Allow"
    bypass         = "AzureServices"
  }

  tags = local.common_tags

  depends_on = [azurerm_role_assignment.current_user_resource_group_contributor]
}

# ============================================================================
# Basic Infrastructure Secrets
# ============================================================================
resource "azurerm_key_vault_secret" "azure_storage_connection_string" {
  name         = "azure-storage-connection-string"
  value        = azurerm_storage_account.main.primary_connection_string
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault.main]
}

resource "azurerm_key_vault_secret" "azure_storage_input_container_name" {
  name         = "azure-storage-input-container-name"
  value        = azurerm_storage_container.input.name
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault.main]
}

resource "azurerm_key_vault_secret" "azure_storage_output_container_name" {
  name         = "azure-storage-output-container-name"
  value        = azurerm_storage_container.output.name
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault.main]
}

# ============================================================================
# Key Vault Secrets - AI Services (created after AI resources)
# ============================================================================
resource "azurerm_key_vault_secret" "ai_secrets" {
  for_each = local.ai_secrets

  name         = each.key
  value        = each.value.value
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [
    azurerm_key_vault.main,
    azapi_resource.ai_foundry_account,
    azapi_resource.model_deployments
  ]
}

# ============================================================================
# Key Vault Secrets - Supabase (created after Supabase resources)
# ============================================================================
resource "azurerm_key_vault_secret" "supabase_secrets" {
  for_each = local.supabase_secrets

  name         = each.key
  value        = each.value.value
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [supabase_project.main, azurerm_key_vault.main]
}

# ============================================================================
# Database URL from Supabase Session Pooler Connection String
# Using session pooler (port 5432) which supports IPv4 without requiring IPv4 add-on
# This avoids IPv6 connection issues on Azure App Service
# ============================================================================
resource "azurerm_key_vault_secret" "database_url" {
  name         = "database-url"
  value        = "postgresql+psycopg2://postgres.${supabase_project.main.id}:${var.supabase_database_password}@aws-1-${var.supabase_region}.pooler.supabase.com:5432/postgres"
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [supabase_project.main, azurerm_key_vault.main]
}

