data "azurerm_client_config" "current" {}

# ============================================================================
# RBAC Assignments - Using for_each to reduce repetition
# ============================================================================

locals {
  # Key Vault role assignments
  key_vault_assignments = {
    "server-app-secrets-user" = {
  scope                = var.key_vault_id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = var.server_app_identity_principal_id
}
    "current-user-secrets-officer" = {
  scope                = var.key_vault_id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}
    "current-user-reader" = {
  scope                = var.key_vault_id
  role_definition_name = "Key Vault Reader"
  principal_id         = data.azurerm_client_config.current.object_id
}
  }

  # ACR role assignments
  acr_assignments = {
    "server-app-pull" = {
  scope                = var.acr_id
  role_definition_name = "AcrPull"
  principal_id         = var.server_app_identity_principal_id
}
    "web-app-pull" = {
  scope                = var.acr_id
  role_definition_name = "AcrPull"
  principal_id         = var.web_app_identity_principal_id
}
    "current-user-push" = {
  scope                = var.acr_id
  role_definition_name = "AcrPush"
  principal_id         = data.azurerm_client_config.current.object_id
}
    "current-user-pull" = {
  scope                = var.acr_id
  role_definition_name = "AcrPull"
  principal_id         = data.azurerm_client_config.current.object_id
}
  }

  # Storage Account role assignments
  storage_assignments = {
    "server-app-blob-contributor" = {
  scope                = var.storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = var.server_app_identity_principal_id
}
    "current-user-blob-contributor" = {
  scope                = var.storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}
  }

  # AI Foundry (Cognitive Services) role assignments
  ai_assignments = {
    "current-user-contributor" = {
  scope                = var.ai_foundry_cognitive_account_id
  role_definition_name = "Cognitive Services Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}
    "current-user-openai-contributor" = {
  scope                = var.ai_foundry_cognitive_account_id
  role_definition_name = "Cognitive Services OpenAI Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}
    "server-app-openai-user" = {
  scope                = var.ai_foundry_cognitive_account_id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = var.server_app_identity_principal_id
    }
  }
}

# Key Vault RBAC
resource "azurerm_role_assignment" "key_vault" {
  for_each = local.key_vault_assignments

  scope                = each.value.scope
  role_definition_name = each.value.role_definition_name
  principal_id         = each.value.principal_id

  lifecycle {
    ignore_changes = [
      condition_version,
      skip_service_principal_aad_check
    ]
  }
}

# ACR RBAC
resource "azurerm_role_assignment" "acr" {
  for_each = local.acr_assignments

  scope                = each.value.scope
  role_definition_name = each.value.role_definition_name
  principal_id         = each.value.principal_id

  lifecycle {
    ignore_changes = [
      condition_version,
      skip_service_principal_aad_check
    ]
  }
}

# Storage Account RBAC
resource "azurerm_role_assignment" "storage" {
  for_each = local.storage_assignments

  scope                = each.value.scope
  role_definition_name = each.value.role_definition_name
  principal_id         = each.value.principal_id

  lifecycle {
    ignore_changes = [
      condition_version,
      skip_service_principal_aad_check
    ]
  }
}

# AI Foundry RBAC
resource "azurerm_role_assignment" "ai" {
  for_each = local.ai_assignments

  scope                = each.value.scope
  role_definition_name = each.value.role_definition_name
  principal_id         = each.value.principal_id

  lifecycle {
    ignore_changes = [
      condition_version,
      skip_service_principal_aad_check
    ]
  }
}

