# ============================================================================
# Role-Based Access Control (RBAC) Assignments
# ============================================================================

locals {
  # Key Vault role assignments
  # Current user: Key Vault Secrets Officer (can do everything)
  # API & Worker: Key Vault Secrets User (read secret values)
  key_vault_assignments = {
    "api-secrets-user" = {
      scope                = azurerm_key_vault.main.id
      role_definition_name = "Key Vault Secrets User"
      principal_id         = azurerm_user_assigned_identity.api.principal_id
    }
    "worker-secrets-user" = {
      scope                = azurerm_key_vault.main.id
      role_definition_name = "Key Vault Secrets User"
      principal_id         = azurerm_user_assigned_identity.worker.principal_id
    }
    "current-user-secrets-officer" = {
      scope                = azurerm_key_vault.main.id
      role_definition_name = "Key Vault Secrets Officer"
      principal_id         = data.azurerm_client_config.current.object_id
    }
  }

  # ACR role assignments
  # Note: api and worker AcrPull are handled in container-app.tf to ensure they're created before container apps
  acr_assignments = {
    "web-app-pull" = {
      scope                = azurerm_container_registry.acr.id
      role_definition_name = "AcrPull"
      principal_id         = azurerm_linux_web_app.web.identity[0].principal_id
    }
    "current-user-push" = {
      scope                = azurerm_container_registry.acr.id
      role_definition_name = "AcrPush"
      principal_id         = data.azurerm_client_config.current.object_id
    }
    "current-user-pull" = {
      scope                = azurerm_container_registry.acr.id
      role_definition_name = "AcrPull"
      principal_id         = data.azurerm_client_config.current.object_id
    }
  }

  # Storage Account role assignments
  # API & Worker: Storage Blob Data Contributor + Storage Queue Data Contributor
  storage_assignments = {
    "api-blob-contributor" = {
      scope                = azurerm_storage_account.main.id
      role_definition_name = "Storage Blob Data Contributor"
      principal_id         = azurerm_user_assigned_identity.api.principal_id
    }
    "api-queue-contributor" = {
      scope                = azurerm_storage_account.main.id
      role_definition_name = "Storage Queue Data Contributor"
      principal_id         = azurerm_user_assigned_identity.api.principal_id
    }
    "worker-blob-contributor" = {
      scope                = azurerm_storage_account.main.id
      role_definition_name = "Storage Blob Data Contributor"
      principal_id         = azurerm_user_assigned_identity.worker.principal_id
    }
    "worker-queue-contributor" = {
      scope                = azurerm_storage_account.main.id
      role_definition_name = "Storage Queue Data Contributor"
      principal_id         = azurerm_user_assigned_identity.worker.principal_id
    }
  }

  # AI Foundry (Cognitive Services) role assignments
  # Current user: Cognitive Services Contributor + OpenAI Contributor (can manage AI models)
  # API & Worker: Cognitive Services OpenAI User (use AI models)
  ai_assignments = {
    "current-user-contributor" = {
      scope                = azapi_resource.ai_foundry_account.id
      role_definition_name = "Cognitive Services Contributor"
      principal_id         = data.azurerm_client_config.current.object_id
    }
    "current-user-openai-contributor" = {
      scope                = azapi_resource.ai_foundry_account.id
      role_definition_name = "Cognitive Services OpenAI Contributor"
      principal_id         = data.azurerm_client_config.current.object_id
    }
    "api-openai-user" = {
      scope                = azapi_resource.ai_foundry_account.id
      role_definition_name = "Cognitive Services OpenAI User"
      principal_id         = azurerm_user_assigned_identity.api.principal_id
    }
    "worker-openai-user" = {
      scope                = azapi_resource.ai_foundry_account.id
      role_definition_name = "Cognitive Services OpenAI User"
      principal_id         = azurerm_user_assigned_identity.worker.principal_id
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

