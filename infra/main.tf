# Resource Group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location

  tags = {
    environment = var.environment
    project     = var.project_name
  }
}

# PostgreSQL Flexible Server with Serverless Compute
resource "azurerm_postgresql_flexible_server" "main" {
  name                = "${var.project_name}-${var.environment}-${random_string.suffix.result}-db"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  version             = "16"

  administrator_login    = var.database_admin_username
  administrator_password = var.database_admin_password

  storage_mb   = 32768
  storage_tier = "P4"

  # Use Burstable tier for cost-effective serverless workloads
  sku_name = "B_Standard_B1ms"

  auto_grow_enabled            = true
  backup_retention_days        = 7
  geo_redundant_backup_enabled = false

  tags = {
    environment = var.environment
    project     = var.project_name
  }

  lifecycle {
    ignore_changes = [zone]
  }
}

# PostgreSQL Database
resource "azurerm_postgresql_flexible_server_database" "main" {
  name      = "${var.project_name}-${var.environment}-${random_string.suffix.result}-db"
  server_id = azurerm_postgresql_flexible_server.main.id
  collation = "en_US.utf8"
  charset   = "utf8"
}

# Firewall rule to allow Azure services
resource "azurerm_postgresql_flexible_server_firewall_rule" "azure_services" {
  name             = "${var.project_name}-${var.environment}-${random_string.suffix.result}-db-allow-azure-services"
  server_id        = azurerm_postgresql_flexible_server.main.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# Azure OpenAI (AI Foundry)
resource "azurerm_cognitive_account" "openai" {
  name                = "${var.project_name}-${var.environment}-${random_string.suffix.result}-openai"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  kind                = "OpenAI"
  sku_name            = "S0"

  tags = {
    environment = var.environment
    project     = var.project_name
  }
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

  sku {
    name = "Standard"
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

  sku {
    name = "Standard"
  }
}

# Storage Account for Blob Storage
resource "azurerm_storage_account" "main" {
  name                     = "${replace(var.project_name, "-", "")}${var.environment}${random_string.suffix.result}sa"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = {
    environment = var.environment
    project     = var.project_name
  }
}

# Blob Containers
resource "azurerm_storage_container" "documents" {
  name                  = "documents"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

# Azure AI Search Service
resource "azurerm_search_service" "main" {
  name                = "${replace(var.project_name, "-", "")}${var.environment}${random_string.suffix.result}search"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "basic"  # Use standard for production, basic for dev

  tags = {
    environment = var.environment
    project     = var.project_name
  }
}

# Azure AI Document Intelligence
resource "azurerm_cognitive_account" "document_intelligence" {
  name                = "${var.project_name}-${var.environment}-${random_string.suffix.result}-docintel"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  kind                = "FormRecognizer"
  sku_name            = "S0"

  tags = {
    environment = var.environment
    project     = var.project_name
  }
}

# Random string for unique naming
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}
