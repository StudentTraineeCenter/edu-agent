# ============================================================================
# User-Assigned Managed Identities for Container Apps
# ============================================================================
resource "azurerm_user_assigned_identity" "api" {
  name                = "${local.api_container_app_name}-identity"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  tags = local.common_tags
}

resource "azurerm_user_assigned_identity" "worker" {
  name                = "${local.worker_container_app_name}-identity"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  tags = local.common_tags
}

# ============================================================================
# Grant AcrPull role to the managed identities
# ============================================================================
# This must be done before the container apps try to pull images
resource "azurerm_role_assignment" "api_acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.api.principal_id
}

resource "azurerm_role_assignment" "worker_acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.worker.principal_id
}

# ============================================================================
# Container App Environment
# ============================================================================
resource "azurerm_container_app_environment" "main" {
  name                       = local.container_app_environment_name
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  tags = local.common_tags
}

# ============================================================================
# Container App for API
# ============================================================================
resource "azurerm_container_app" "api" {
  name                         = local.api_container_app_name
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.api.id]
  }

  registry {
    server   = azurerm_container_registry.acr.login_server
    identity = azurerm_user_assigned_identity.api.id
  }

  depends_on = [azurerm_role_assignment.api_acr_pull]

  ingress {
    external_enabled = true
    target_port      = var.api_target_port
    transport        = "auto"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  template {
    min_replicas = var.api_min_replicas
    max_replicas = var.api_max_replicas

    container {
      name   = local.api_container_app_name
      image  = "${azurerm_container_registry.acr.login_server}/${var.acr_repository_api}:${var.acr_tag_api}"
      cpu    = var.api_cpu
      memory = var.api_memory

      env {
        name  = "AZURE_KEY_VAULT_URI"
        value = azurerm_key_vault.main.vault_uri
      }

      env {
        name  = "AZURE_CLIENT_ID"
        value = azurerm_user_assigned_identity.api.client_id
      }

      env {
        name  = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        value = azurerm_application_insights.main.connection_string
      }

      env {
        name  = "AZURE_STORAGE_ACCOUNT_NAME"
        value = azurerm_storage_account.main.name
      }

      env {
        name  = "AZURE_STORAGE_QUEUE_NAME"
        value = azurerm_storage_queue.ai_generation_tasks.name
      }

      env {
        name  = "CORS_ALLOWED_ORIGINS"
        value = "https://${local.web_app_name}.azurewebsites.net,http://localhost:3000"
      }

      env {
        name  = "MAX_CHAT_MESSAGES_PER_DAY"
        value = var.max_chat_messages_per_day
      }

      env {
        name  = "MAX_FLASHCARD_GENERATIONS_PER_DAY"
        value = var.max_flashcard_generations_per_day
      }

      env {
        name  = "MAX_QUIZ_GENERATIONS_PER_DAY"
        value = var.max_quiz_generations_per_day
      }

      env {
        name  = "MAX_DOCUMENT_UPLOADS_PER_DAY"
        value = var.max_document_uploads_per_day
      }

      # Add all other environment variables from app_settings
      dynamic "env" {
        for_each = var.api_additional_env_vars
        content {
          name  = env.key
          value = env.value
        }
      }
    }
  }

  tags = local.common_tags
}

# ============================================================================
# Container App for Worker
# ============================================================================
resource "azurerm_container_app" "worker" {
  name                         = local.worker_container_app_name
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.worker.id]
  }

  registry {
    server   = azurerm_container_registry.acr.login_server
    identity = azurerm_user_assigned_identity.worker.id
  }

  depends_on = [azurerm_role_assignment.worker_acr_pull]

  # Worker doesn't need ingress (no external access)
  # Ingress block is omitted for internal-only container apps

  template {
    min_replicas = var.worker_min_replicas
    max_replicas = var.worker_max_replicas

    container {
      name   = local.worker_container_app_name
      image  = "${azurerm_container_registry.acr.login_server}/${var.acr_repository_worker}:${var.acr_tag_worker}"
      cpu    = var.worker_cpu
      memory = var.worker_memory

      env {
        name  = "AZURE_KEY_VAULT_URI"
        value = azurerm_key_vault.main.vault_uri
      }

      env {
        name  = "AZURE_CLIENT_ID"
        value = azurerm_user_assigned_identity.worker.client_id
      }

      env {
        name  = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        value = azurerm_application_insights.main.connection_string
      }

      env {
        name  = "AZURE_STORAGE_ACCOUNT_NAME"
        value = azurerm_storage_account.main.name
      }

      env {
        name  = "AZURE_STORAGE_QUEUE_NAME"
        value = azurerm_storage_queue.ai_generation_tasks.name
      }

      # Add all other environment variables from app_settings
      dynamic "env" {
        for_each = var.worker_additional_env_vars
        content {
          name  = env.key
          value = env.value
        }
      }
    }
  }

  tags = local.common_tags
}
