# ============================================================================
# Azure AI Foundry (Cognitive Services)
# ============================================================================
# Next-gen AI Foundry resource with AIServices kind for hosted agents support.
# Uses azapi_resource for better control and access to preview features.

# ============================================================================
# Get Current Client Configuration
# ============================================================================
data "azurerm_client_config" "current" {}

# ============================================================================
# Get Resource Group
# ============================================================================
data "azurerm_resource_group" "main" {
  name = var.resource_group_name
}

# ============================================================================
# AI Services Account (Foundry Hub)
# ============================================================================
resource "azapi_resource" "ai_foundry_account" {
  type      = "Microsoft.CognitiveServices/accounts@2025-04-01-preview"
  name      = var.ai_foundry_hub_name
  location  = var.location
  parent_id = data.azurerm_resource_group.main.id

  identity {
    type = "SystemAssigned"
  }

  body = {
    kind = "AIServices"
    sku = {
      name = "S0"
    }
    properties = {
      customSubDomainName    = var.ai_foundry_hub_name
      publicNetworkAccess    = "Enabled"
      disableLocalAuth        = false
      allowProjectManagement  = true
    }
  }

  tags = var.tags

  response_export_values = [
    "properties.endpoint",
    "properties.endpoints",
    "identity.principalId"
  ]
}

# ============================================================================
# AI Foundry Project
# ============================================================================
resource "azapi_resource" "ai_foundry_project" {
  type      = "Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview"
  name      = var.ai_foundry_project_name
  location  = var.location
  parent_id = azapi_resource.ai_foundry_account.id

  identity {
    type = "SystemAssigned"
  }

  body = {
    properties = {}
  }

  response_export_values = [
    "properties.endpoints",
    "identity.principalId"
  ]
}

# ============================================================================
# Model Deployments
# ============================================================================
# Use for_each to eliminate repetition and make it easier to add/remove models
# Capacity is specified in thousands (e.g., 1 = 1,000 tokens/minute).
# Higher capacity = higher throughput but also higher cost.

locals {
  model_deployments = {
    gpt4o = {
      name    = var.gpt4o_deployment_name
      model   = {
        format  = "OpenAI"
        name    = var.gpt4o_model_name
        version = var.gpt4o_model_version
      }
      sku = {
        name     = var.gpt4o_sku_name
        capacity = var.gpt4o_sku_capacity
      }
    }
    text-embedding-3-large = {
      name    = var.text_embedding_deployment_name
      model   = {
        format  = "OpenAI"
        name    = var.text_embedding_model_name
        version = var.text_embedding_model_version
      }
      sku = {
        name     = var.text_embedding_sku_name
        capacity = var.text_embedding_sku_capacity
      }
    }
  }
}

resource "azapi_resource" "model_deployments" {
  for_each = local.model_deployments

  type      = "Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview"
  name      = each.value.name
  parent_id = azapi_resource.ai_foundry_account.id

  body = {
    sku = {
      name     = each.value.sku.name
      capacity = each.value.sku.capacity
    }
    properties = {
      model = {
        format  = each.value.model.format
        name    = each.value.model.name
        version = each.value.model.version
      }
      versionUpgradeOption = "OnceCurrentVersionExpired"
    }
  }

  # Deployments must be created sequentially
  depends_on = [
    azapi_resource.ai_foundry_project
  ]
}

# ============================================================================
# Get API Keys via Data Source
# ============================================================================
# azapi_resource doesn't expose API keys directly, so we use azurerm data source
# to retrieve them for backward compatibility
data "azurerm_cognitive_account" "ai_foundry_keys" {
  name                = var.ai_foundry_hub_name
  resource_group_name = var.resource_group_name

  depends_on = [azapi_resource.ai_foundry_account]
}

# ============================================================================
# Computed Locals for Endpoints
# ============================================================================
locals {
  # Main AI Services endpoint
  ai_foundry_endpoint = azapi_resource.ai_foundry_account.output.properties.endpoint

  # AI Foundry API endpoint for projects
  ai_foundry_project_endpoint = "https://${var.ai_foundry_hub_name}.services.ai.azure.com/api/projects/${var.ai_foundry_project_name}"

  # OpenAI endpoint for chat completions
  azure_openai_endpoint = "https://${var.ai_foundry_hub_name}.openai.azure.com/"

  # Foundry account principal ID (for RBAC)
  ai_foundry_account_principal_id = azapi_resource.ai_foundry_account.output.identity.principalId

  # Foundry project principal ID (for RBAC)
  ai_foundry_project_principal_id = azapi_resource.ai_foundry_project.output.identity.principalId
}

