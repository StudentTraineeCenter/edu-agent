# ============================================================================
# Azure AI Foundry (Cognitive Services)
# ============================================================================
# Next-gen AI Foundry resource with AIServices kind for hosted agents support.
# Uses azapi_resource for better control and access to preview features.

# ============================================================================
# AI Services Account (Foundry Hub)
# ============================================================================
resource "azapi_resource" "ai_foundry_account" {
  type      = "Microsoft.CognitiveServices/accounts@2025-04-01-preview"
  name      = local.ai_foundry_hub_name
  location  = var.location
  parent_id = azurerm_resource_group.main.id

  identity {
    type = "SystemAssigned"
  }

  body = {
    kind = "AIServices"
    sku = {
      name = "S0"
    }
    properties = {
      customSubDomainName    = local.ai_foundry_hub_name
      publicNetworkAccess    = "Enabled"
      disableLocalAuth        = false
      allowProjectManagement  = true
    }
  }

  tags = local.common_tags

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
  name      = "${local.org_short}-${local.env_short}-project"
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
  name                = local.ai_foundry_hub_name
  resource_group_name = azurerm_resource_group.main.name

  depends_on = [azapi_resource.ai_foundry_account]
}

