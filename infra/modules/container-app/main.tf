# ============================================================================
# User-Assigned Managed Identity for Container App
# ============================================================================
resource "azurerm_user_assigned_identity" "container_app" {
  name                = "${var.app_name}-identity"
  location            = var.location
  resource_group_name = var.resource_group_name

  tags = var.tags
}

# ============================================================================
# Grant AcrPull role to the managed identity
# ============================================================================
# This must be done before the container app tries to pull images
resource "azurerm_role_assignment" "acr_pull" {
  scope                = var.acr_id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.container_app.principal_id
}

# ============================================================================
# Container App Environment
# ============================================================================
resource "azurerm_container_app_environment" "main" {
  name                       = var.environment_name
  location                   = var.location
  resource_group_name        = var.resource_group_name
  log_analytics_workspace_id = var.log_analytics_workspace_id

  tags = var.tags
}

# ============================================================================
# Container App for Server
# ============================================================================
resource "azurerm_container_app" "server" {
  name                         = var.app_name
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.container_app.id]
  }

  registry {
    server   = var.acr_login_server
    identity = azurerm_user_assigned_identity.container_app.id
  }

  depends_on = [azurerm_role_assignment.acr_pull]

  ingress {
    external_enabled = true
    target_port      = var.target_port
    transport        = "auto"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  template {
    min_replicas = var.min_replicas
    max_replicas = var.max_replicas

    container {
      name   = var.app_name
      image  = "${var.acr_login_server}/${var.acr_repository}:${var.acr_tag}"
      cpu    = var.cpu
      memory = var.memory

      env {
        name  = "AZURE_KEY_VAULT_URI"
        value = var.key_vault_uri
      }

      env {
        name  = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        value = var.app_insights_connection_string
      }

      env {
        name  = "CORS_ALLOWED_ORIGINS"
        value = var.cors_allowed_origins
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
        for_each = var.additional_env_vars
        content {
          name  = env.key
          value = env.value
        }
      }
    }
  }

  tags = var.tags
}
