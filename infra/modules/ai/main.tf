# AI Foundry resource - a cognitive account with kind="AIServices"
# According to Microsoft docs, AI Foundry is a cognitive account with project_management_enabled=true
# This account hosts OpenAI-compatible model deployments and projects
resource "azurerm_cognitive_account" "ai_foundry" {
  name                      = var.ai_foundry_hub_name
  location                  = var.location
  resource_group_name       = var.resource_group_name
  kind                      = "AIServices"
  sku_name                  = "S0"
  custom_subdomain_name     = var.ai_foundry_hub_name
  project_management_enabled = true

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# AI Foundry Model Deployments (attached to cognitive account)
resource "azurerm_cognitive_deployment" "gpt4o" {
  name                 = var.gpt4o_deployment_name
  cognitive_account_id = azurerm_cognitive_account.ai_foundry.id

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
  cognitive_account_id = azurerm_cognitive_account.ai_foundry.id

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

