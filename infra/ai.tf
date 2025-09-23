# Azure OpenAI (AI Foundry)
resource "azurerm_cognitive_account" "openai" {
  name                = "${local.name_prefix}-openai"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  kind                = "OpenAI"
  sku_name            = "S0"

  tags = local.common_tags
}

# OpenAI Model Deployments
resource "azurerm_cognitive_deployment" "gpt4o_mini" {
  name                 = "gpt-4o-mini"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "gpt-4o-mini"
    version = "2024-07-18"
  }

  scale {
    type = "Standard"
  }
}

resource "azurerm_cognitive_deployment" "text_embedding" {
  name                 = "text-embedding-3-small"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "text-embedding-3-small"
    version = "1"
  }

  scale {
    type = "Standard"
  }
}

# Azure AI Document Intelligence
resource "azurerm_cognitive_account" "document_intelligence" {
  name                = "${local.name_prefix}-docintel"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  kind                = "FormRecognizer"
  sku_name            = "S0"

  tags = local.common_tags
}
