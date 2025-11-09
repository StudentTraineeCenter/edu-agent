# AI Foundry Hub
resource "azurerm_ai_foundry" "hub" {
  name                = var.ai_foundry_hub_name
  location            = var.location
  resource_group_name = var.resource_group_name

  storage_account_id = var.storage_account_id
  key_vault_id       = var.key_vault_id

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# Data source to get cognitive account details (AI Foundry hub is a cognitive account)
data "azurerm_cognitive_account" "hub" {
  name                = azurerm_ai_foundry.hub.name
  resource_group_name = var.resource_group_name
}

# AI Foundry Project
resource "azurerm_ai_foundry_project" "project" {
  name               = var.ai_foundry_project_name
  location           = azurerm_ai_foundry.hub.location
  ai_services_hub_id = azurerm_ai_foundry.hub.id

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# AI Foundry Model Deployments (attached to hub)
resource "azurerm_cognitive_deployment" "gpt4o" {
  name                 = var.gpt4o_deployment_name
  cognitive_account_id = data.azurerm_cognitive_account.hub.id

  model {
    format  = "OpenAI"
    name    = var.gpt4o_model_name
    version = var.gpt4o_model_version
  }

  sku {
    name     = var.gpt4o_sku_name
    capacity = var.gpt4o_sku_capacity
  }
}

resource "azurerm_cognitive_deployment" "text_embedding_3_large" {
  name                 = var.text_embedding_deployment_name
  cognitive_account_id = data.azurerm_cognitive_account.hub.id

  model {
    format  = "OpenAI"
    name    = var.text_embedding_model_name
    version = var.text_embedding_model_version
  }

  sku {
    name     = var.text_embedding_sku_name
    capacity = var.text_embedding_sku_capacity
  }
}

# AI Services
resource "azurerm_ai_services" "service" {
  location            = var.location
  name                = var.ai_services_name
  resource_group_name = var.resource_group_name
  sku_name            = var.ai_services_sku_name

  tags = var.tags
}

