# Random string for unique naming
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# Common locals for consistent naming
locals {
  common_tags = {
    environment = var.environment
    project     = var.project_name
  }

  # CAF naming components
  org_short     = replace(var.project_name, "-", "")
  env_short     = var.environment == "prod" ? "prd" : (var.environment == "staging" ? "stg" : "dev")
  region_short  = var.region_code
  workload_part = var.workload != "" ? "-${var.workload}" : ""
  instance      = random_string.suffix.result

  # CAF naming patterns
  # Resource Group: rg-{org}-{env}-{region}-{workload}
  resource_group_name = "rg-${local.org_short}-${local.env_short}-${local.region_short}${local.workload_part}"

  # Storage Account: st{org}{env}{region}{workload}{instance} (no hyphens, lowercase, max 24 chars)
  storage_account_name = lower(substr("st${local.org_short}${local.env_short}${local.region_short}${replace(local.workload_part, "-", "")}${local.instance}", 0, 24))

  # Container Registry: cr{org}{env}{region}{workload}{instance} (no hyphens, lowercase, max 50 chars)
  acr_name = lower(substr("cr${local.org_short}${local.env_short}${local.region_short}${replace(local.workload_part, "-", "")}${local.instance}", 0, 50))

  # Key Vault: kv-{org}-{env}-{region}-{workload}-{instance} (max 24 chars)
  key_vault_name = substr("kv-${local.org_short}-${local.env_short}-${local.region_short}${local.workload_part}-${local.instance}", 0, 24)

  # App Service Plan: asp-{org}-{env}-{region}-{workload}-{instance} (max 40 chars)
  app_service_plan_name = substr("asp-${local.org_short}-${local.env_short}-${local.region_short}${local.workload_part}-${local.instance}", 0, 40)

  # App Services: app-{org}-{env}-{region}-{workload}-{instance} (max 60 chars)
  api_app_name = substr("app-${local.org_short}-${local.env_short}-${local.region_short}${local.workload_part}-api-${local.instance}", 0, 60)
  web_app_name = substr("app-${local.org_short}-${local.env_short}-${local.region_short}${local.workload_part}-web-${local.instance}", 0, 60)

  # Database: sql-{org}-{env}-{region}-{workload}-{instance} (max 63 chars)
  database_server_name = substr("sql-${local.org_short}-${local.env_short}-${local.region_short}${local.workload_part}-${local.instance}", 0, 63)
  database_name        = substr("sqldb-${local.org_short}-${local.env_short}-${local.region_short}${local.workload_part}-${local.instance}", 0, 63)

  # OpenAI: oai-{org}-{env}-{region}-{workload}-{instance} (max 64 chars)
  openai_account_name = substr("oai-${local.org_short}-${local.env_short}-${local.region_short}${local.workload_part}-${local.instance}", 0, 64)
  openai_subdomain_name = lower(substr("oai${local.org_short}${local.env_short}${local.region_short}${replace(local.workload_part, "-", "")}${local.instance}", 0, 64))

  # AI Foundry Hub: aif-{org}-{env}-{region}-{workload}-{instance} (max 64 chars)
  ai_foundry_hub_name = substr("aif-${local.org_short}-${local.env_short}-${local.region_short}${local.workload_part}-${local.instance}", 0, 64)

  # AI Foundry Project: aifp-{org}-{env}-{region}-{workload}-{instance} (max 64 chars)
  ai_foundry_project_name = substr("aifp-${local.org_short}-${local.env_short}-${local.region_short}${local.workload_part}-${local.instance}", 0, 64)

  # AI Services: cog-{org}-{env}-{region}-{workload}-{instance} (max 64 chars)
  ai_services_name = substr("cog-${local.org_short}-${local.env_short}-${local.region_short}${local.workload_part}-${local.instance}", 0, 64)
}

# Resource Group Module
module "resource_group" {
  source = "./modules/resource-group"

  name     = local.resource_group_name
  location = var.location
  tags     = local.common_tags
}

# Storage Module
module "storage" {
  source = "./modules/storage"

  storage_account_name = local.storage_account_name
  resource_group_name  = module.resource_group.name
  location             = module.resource_group.location
  tags                 = local.common_tags
}

# ACR Module
module "acr" {
  source = "./modules/acr"

  acr_name          = local.acr_name
  resource_group_name = module.resource_group.name
  location          = module.resource_group.location
  tags              = local.common_tags
}

# Key Vault Module
module "key_vault" {
  source = "./modules/key-vault"

  key_vault_name    = local.key_vault_name
  resource_group_name = module.resource_group.name
  location          = module.resource_group.location
  tags              = local.common_tags
}

# Database Module (DISABLED)
# Uncomment and provide database_admin_username and database_admin_password variables to enable
# module "database" {
#   source = "./modules/database"
#
#   server_name         = local.database_server_name
#   resource_group_name = module.resource_group.name
#   location            = module.resource_group.location
#   database_name       = local.database_name
#   firewall_rule_name  = "${local.database_server_name}-fw-azure"
#   administrator_login    = var.database_admin_username
#   administrator_password = var.database_admin_password
#   tags                = local.common_tags
# }

# AI Module
module "ai" {
  source = "./modules/ai"

  location            = module.resource_group.location
  resource_group_name = module.resource_group.name
  openai_account_name = local.openai_account_name
  openai_custom_subdomain_name = local.openai_subdomain_name
  ai_foundry_hub_name = local.ai_foundry_hub_name
  ai_foundry_project_name = local.ai_foundry_project_name
  ai_services_name    = local.ai_services_name
  storage_account_id  = module.storage.storage_account_id
  key_vault_id        = module.key_vault.id
  tags                = local.common_tags
}

# App Service Module
module "app_service" {
  source = "./modules/app-service"

  service_plan_name = local.app_service_plan_name
  location          = module.resource_group.location
  resource_group_name = module.resource_group.name
  api_app_name      = local.api_app_name
  web_app_name      = local.web_app_name
  acr_login_server  = module.acr.login_server
  acr_repository_api = var.acr_repository_api
  acr_tag_api       = var.acr_tag_api
  acr_repository_web = var.acr_repository_web
  acr_tag_web       = var.acr_tag_web

  api_app_settings = {
    # PostgreSQL
    "POSTGRES_DB"       = "postgres"
    "POSTGRES_USER"     = "postgres"
    "POSTGRES_PASSWORD" = "postgres"
    "POSTGRES_HOST"     = "127.0.0.1"
    "POSTGRES_PORT"     = "5432"
    "DATABASE_URL"      = "postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/postgres"

    # Azure OpenAI
    "AZURE_OPENAI_ENDPOINT"             = module.ai.openai_endpoint
    "AZURE_OPENAI_API_KEY"              = module.ai.openai_api_key
    "AZURE_OPENAI_DEFAULT_MODEL"        = module.ai.gpt4o_deployment_name
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT" = module.ai.text_embedding_3_large_deployment_name
    "AZURE_OPENAI_CHAT_DEPLOYMENT"      = module.ai.gpt4o_deployment_name
    "AZURE_OPENAI_API_VERSION"          = "2024-06-01"

    # Azure Storage
    "AZURE_STORAGE_CONNECTION_STRING" = module.storage.primary_connection_string
    "AZURE_STORAGE_CONTAINER_NAME"    = module.storage.container_name
    "AZURE_STORAGE_ACCOUNT_KEY"       = module.storage.primary_access_key

    # Azure Content Understanding (AI Services)
    "AZURE_CU_KEY"         = module.ai.ai_service_key
    "AZURE_CU_ENDPOINT"    = module.ai.ai_service_endpoint
    "AZURE_CU_ANALYZER_ID" = "prebuilt-documentAnalyzer"

    # Azure Entra ID
    "AZURE_ENTRA_TENANT_ID" = var.azure_tenant_id
    "AZURE_ENTRA_CLIENT_ID" = data.azurerm_client_config.current.client_id

    # Required for Python web apps
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "true"
    "WEBSITES_PORT"                  = "8000"
    "STARTUP_COMMAND"                = "gunicorn -k uvicorn.workers.UvicornWorker -w 2 app.main:app --bind 0.0.0.0:8000"
  }

  web_app_settings = {
    "WEBSITES_PORT"                       = "80"
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = "false"

    # Frontend environment variables
    "VITE_AZURE_ENTRA_TENANT_ID" = var.azure_tenant_id
    "VITE_AZURE_ENTRA_CLIENT_ID" = var.azure_app_client_id

    # URLs — constructed from name pattern (will match actual hostname)
    "VITE_SERVER_URL" = "https://${local.api_app_name}.azurewebsites.net"
  }

  tags = local.common_tags
}

# RBAC Module
module "rbac" {
  source = "./modules/rbac"

  acr_id                        = module.acr.id
  api_app_identity_principal_id = module.app_service.api_app_identity_principal_id
  web_app_identity_principal_id = module.app_service.web_app_identity_principal_id
  storage_account_id            = module.storage.storage_account_id
  openai_account_id             = module.ai.openai_account_id
}

# Data source for current client config
data "azurerm_client_config" "current" {}

