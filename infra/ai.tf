# Azure OpenAI (AI Foundry)
resource "azurerm_cognitive_account" "openai" {
  name                  = "${local.name_prefix}-openai"
  location              = azurerm_resource_group.main.location
  resource_group_name   = azurerm_resource_group.main.name
  kind                  = "OpenAI"
  sku_name              = "S0"
  custom_subdomain_name = "${local.name_prefix}-openai"

  tags = local.common_tags
}

# OpenAI Model Deployments for RAG
resource "azurerm_cognitive_deployment" "gpt4o" {
  name                 = "gpt-4o"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "gpt-4o"
    version = "2024-11-20"
  }

  sku {
    name     = "GlobalStandard"
    capacity = 1
  }
}

resource "azurerm_cognitive_deployment" "text_embedding_3_large" {
  name                 = "text-embedding-3-large"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "text-embedding-3-large"
    version = "1"
  }

  sku {
    name     = "GlobalStandard"
    capacity = 1
  }
}

resource "azurerm_ai_foundry" "hub" {
  name                = "${local.name_prefix}-foundry-hub"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  storage_account_id = azurerm_storage_account.main.id
  key_vault_id       = azurerm_key_vault.main.id

  identity {
    type = "SystemAssigned"
  }

  tags = local.common_tags
}

resource "azurerm_ai_foundry_project" "project" {
  name               = "${local.name_prefix}-project"
  location           = azurerm_ai_foundry.hub.location
  ai_services_hub_id = azurerm_ai_foundry.hub.id

  identity {
    type = "SystemAssigned"
  }

  tags = local.common_tags
}

resource "azurerm_ai_services" "service" {
  location            = azurerm_resource_group.main.location
  name                = "${local.name_prefix}-ai-service"
  resource_group_name = azurerm_resource_group.main.name
  sku_name            = "S0"
}
