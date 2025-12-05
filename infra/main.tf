# ============================================================================
# Random Suffix for Unique Resource Naming
# ============================================================================
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# ============================================================================
# Common Locals for Consistent Naming (CAF Naming Convention)
# ============================================================================
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

  # CAF naming patterns following Azure naming conventions
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
  server_app_name = substr("app-${local.org_short}-${local.env_short}-${local.region_short}${local.workload_part}-server-${local.instance}", 0, 60)
  web_app_name    = substr("app-${local.org_short}-${local.env_short}-${local.region_short}${local.workload_part}-web-${local.instance}", 0, 60)

  # Database: sql-{org}-{env}-{region}-{workload}-{instance} (max 63 chars)
  database_server_name = substr("sql-${local.org_short}-${local.env_short}-${local.region_short}${local.workload_part}-${local.instance}", 0, 63)
  database_name        = substr("sqldb-${local.org_short}-${local.env_short}-${local.region_short}${local.workload_part}-${local.instance}", 0, 63)

  # AI Foundry Hub: aif-{org}-{env}-{region}-{workload}-{instance} (max 64 chars)
  ai_foundry_hub_name = substr("aif-${local.org_short}-${local.env_short}-${local.region_short}${local.workload_part}-${local.instance}", 0, 64)

  # AI Services: cog-{org}-{env}-{region}-{workload}-{instance} (max 64 chars)
  ai_services_name = substr("cog-${local.org_short}-${local.env_short}-${local.region_short}${replace(local.workload_part, "-", "")}${local.instance}", 0, 64)

  # Application Insights: appi-{org}-{env}-{region}-{workload}-{instance} (max 260 chars)
  app_insights_name = substr("appi-${local.org_short}-${local.env_short}-${local.region_short}${local.workload_part}-${local.instance}", 0, 260)

  # Log Analytics Workspace: law-{org}-{env}-{region}-{workload}-{instance} (max 63 chars)
  log_analytics_workspace_name = substr("law-${local.org_short}-${local.env_short}-${local.region_short}${local.workload_part}-${local.instance}", 0, 63)
}

# ============================================================================
# Resource Group
# ============================================================================
module "resource_group" {
  source = "./modules/resource-group"

  name     = local.resource_group_name
  location = var.location
  tags     = local.common_tags
}

# ============================================================================
# Storage Account
# ============================================================================
module "storage" {
  source = "./modules/storage"

  storage_account_name = local.storage_account_name
  resource_group_name  = module.resource_group.name
  location             = module.resource_group.location
  tags                 = local.common_tags
}

# ============================================================================
# Azure Container Registry
# ============================================================================
module "acr" {
  source = "./modules/acr"

  acr_name            = local.acr_name
  resource_group_name = module.resource_group.name
  location            = module.resource_group.location
  tags                = local.common_tags
}

# ============================================================================
# Grant Current User Full Access to Resource Group
# This ensures the user running Terraform has permissions to manage all resources
# ============================================================================
data "azurerm_client_config" "current" {}

resource "azurerm_role_assignment" "current_user_resource_group_contributor" {
  scope                = module.resource_group.id
  role_definition_name = "Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
  
  depends_on = [module.resource_group]
}

# ============================================================================
# Key Vault Module
# Note: AI-related secrets and Supabase database URL are created separately 
# in main.tf after their respective modules are created
# ============================================================================
module "key_vault" {
  source = "./modules/key-vault"

  key_vault_name      = local.key_vault_name
  resource_group_name = module.resource_group.name
  location            = module.resource_group.location
  tags                = local.common_tags

  # Basic infrastructure secrets (non-AI, non-Supabase)
  # database_url will be set from Supabase connection string after Supabase is created
  database_url                         = null  # Will be replaced by Supabase connection string
  azure_storage_connection_string      = module.storage.primary_connection_string
  azure_storage_input_container_name   = module.storage.input_container_name
  azure_storage_output_container_name = module.storage.output_container_name
  
  depends_on = [azurerm_role_assignment.current_user_resource_group_contributor]
}

# ============================================================================
# Key Vault RBAC - Grant Terraform service principal access immediately
# This ensures RBAC is set up before any secret operations
# ============================================================================
resource "azurerm_role_assignment" "terraform_key_vault_secrets_officer" {
  scope                = module.key_vault.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
  
  depends_on = [module.key_vault]
}

# ============================================================================
# Azure AI Services (AI Foundry & Cognitive Services)
# ============================================================================
module "ai" {
  source = "./modules/ai"

  location            = module.resource_group.location
  resource_group_name = module.resource_group.name
  ai_foundry_hub_name = local.ai_foundry_hub_name
  ai_services_name    = local.ai_services_name
  storage_account_id  = module.storage.storage_account_id
  key_vault_id        = module.key_vault.id
  tags                = local.common_tags
}

# ============================================================================
# Key Vault Secrets - AI Services (created after AI module)
# ============================================================================
resource "azurerm_key_vault_secret" "azure_openai_api_key" {
  name         = "azure-openai-api-key"
  value        = module.ai.ai_foundry_api_key
  key_vault_id = module.key_vault.id

  depends_on = [module.ai, module.key_vault]
}

resource "azurerm_key_vault_secret" "azure_openai_endpoint" {
  name         = "azure-openai-endpoint"
  value        = module.ai.ai_foundry_endpoint
  key_vault_id = module.key_vault.id

  depends_on = [module.ai, module.key_vault]
}

resource "azurerm_key_vault_secret" "azure_openai_default_model" {
  name         = "azure-openai-default-model"
  value        = module.ai.gpt4o_deployment_name
  key_vault_id = module.key_vault.id

  depends_on = [module.ai, module.key_vault]
}

resource "azurerm_key_vault_secret" "azure_openai_embedding_deployment" {
  name         = "azure-openai-embedding-deployment"
  value        = module.ai.text_embedding_3_large_deployment_name
  key_vault_id = module.key_vault.id

  depends_on = [module.ai, module.key_vault]
}

resource "azurerm_key_vault_secret" "azure_openai_chat_deployment" {
  name         = "azure-openai-chat-deployment"
  value        = module.ai.gpt4o_deployment_name
  key_vault_id = module.key_vault.id

  depends_on = [module.ai, module.key_vault]
}

resource "azurerm_key_vault_secret" "azure_openai_api_version" {
  name         = "azure-openai-api-version"
  value        = "2024-06-01"
  key_vault_id = module.key_vault.id

  depends_on = [module.key_vault]
}

resource "azurerm_key_vault_secret" "azure_document_intelligence_endpoint" {
  name         = "azure-document-intelligence-endpoint"
  value        = module.ai.ai_service_endpoint
  key_vault_id = module.key_vault.id

  depends_on = [module.ai, module.key_vault]
}

resource "azurerm_key_vault_secret" "azure_document_intelligence_key" {
  name         = "azure-document-intelligence-key"
  value        = module.ai.ai_service_key
  key_vault_id = module.key_vault.id

  depends_on = [module.ai, module.key_vault]
}

resource "azurerm_key_vault_secret" "azure_cu_endpoint" {
  name         = "azure-cu-endpoint"
  value        = module.ai.ai_service_endpoint
  key_vault_id = module.key_vault.id

  depends_on = [module.ai, module.key_vault]
}

resource "azurerm_key_vault_secret" "azure_cu_key" {
  name         = "azure-cu-key"
  value        = module.ai.ai_service_key
  key_vault_id = module.key_vault.id

  depends_on = [module.ai, module.key_vault]
}

resource "azurerm_key_vault_secret" "azure_cu_analyzer_id" {
  name         = "azure-cu-analyzer-id"
  value        = "prebuilt-documentAnalyzer"
  key_vault_id = module.key_vault.id

  depends_on = [module.key_vault]
}

# ============================================================================
# Supabase Project
# Note: Site URL will be updated after app service is created via a separate
# terraform apply or manually in Supabase dashboard
# ============================================================================
module "supabase" {
  source = "./modules/supabase"

  supabase_organization_id = var.supabase_organization_id
  project_name            = "${local.org_short}-${local.env_short}"
  database_password       = var.supabase_database_password
  region                  = var.supabase_region
  # Site URL placeholder - update after app service is created
  # Can be updated via: terraform apply -target=module.supabase.supabase_settings.main
  site_url                = "http://localhost:3000"  # Will be updated after deployment
}

# ============================================================================
# Key Vault Secrets - Supabase (created after Supabase module)
# ============================================================================
resource "azurerm_key_vault_secret" "supabase_url" {
  name         = "supabase-url"
  value        = module.supabase.api_url
  key_vault_id = module.key_vault.id

  depends_on = [module.supabase, module.key_vault]
}

# Supabase API keys and JWT secret
# These can be provided via Terraform variables or updated manually later
resource "azurerm_key_vault_secret" "supabase_service_role_key" {
  name         = "supabase-service-role-key"
  value        = var.supabase_service_role_key != null ? var.supabase_service_role_key : "MANUAL_UPDATE_REQUIRED"
  key_vault_id = module.key_vault.id

  depends_on = [module.supabase, module.key_vault]
}

resource "azurerm_key_vault_secret" "supabase_jwt_secret" {
  name         = "supabase-jwt-secret"
  value        = var.supabase_jwt_secret != null ? var.supabase_jwt_secret : "MANUAL_UPDATE_REQUIRED"
  key_vault_id = module.key_vault.id

  depends_on = [module.supabase, module.key_vault]
}

# ============================================================================
# Database URL from Supabase Session Pooler Connection String
# Using session pooler (port 5432) which supports IPv4 without requiring IPv4 add-on
# This avoids IPv6 connection issues on Azure App Service
# ============================================================================
resource "azurerm_key_vault_secret" "database_url" {
  name         = "database-url"
  value        = module.supabase.database_pooler_connection_string
  key_vault_id = module.key_vault.id

  depends_on = [module.supabase, module.key_vault]
}

# ============================================================================
# Application Insights & Log Analytics
# ============================================================================
module "application_insights" {
  source = "./modules/application-insights"

  app_insights_name            = local.app_insights_name
  log_analytics_workspace_name = local.log_analytics_workspace_name
  location                     = module.resource_group.location
  resource_group_name          = module.resource_group.name
  tags                         = local.common_tags
}

# ============================================================================
# App Service Plan & Web Apps
# ============================================================================
module "app_service" {
  source = "./modules/app-service"

  service_plan_name     = local.app_service_plan_name
  location              = module.resource_group.location
  resource_group_name   = module.resource_group.name
  server_app_name       = local.server_app_name
  web_app_name          = local.web_app_name
  acr_login_server      = module.acr.login_server
  acr_repository_server = var.acr_repository_server
  acr_tag_server        = var.acr_tag_server
  acr_repository_web    = var.acr_repository_web
  acr_tag_web           = var.acr_tag_web

  server_app_settings = {
    # Key Vault configuration - app uses managed identity to fetch secrets via RBAC
    "AZURE_KEY_VAULT_URI" = module.key_vault.uri

    # Application Insights
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = module.application_insights.app_insights_connection_string

    # CORS configuration - allow requests from web app and localhost
    "CORS_ALLOWED_ORIGINS" = "https://${local.web_app_name}.azurewebsites.net,http://localhost:3000"

    # Usage limits (read directly from env, not from Key Vault)
    "MAX_CHAT_MESSAGES_PER_DAY"         = "50"
    "MAX_FLASHCARD_GENERATIONS_PER_DAY" = "10"
    "MAX_QUIZ_GENERATIONS_PER_DAY"      = "10"
    "MAX_DOCUMENT_UPLOADS_PER_DAY"      = "5"

    # Required for Python web apps
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "true"
    "WEBSITES_PORT"                  = "8000"
    # Disable access logging - HTTP logs handled by HTTPLoggingMiddleware and sent to Azure Monitor
    # Note: uvicorn workers will respect access_log=False set in main.py
    "STARTUP_COMMAND"                = "gunicorn -k uvicorn.workers.UvicornWorker -w 2 --log-level info app.main:app --bind 0.0.0.0:8000"
  }

  depends_on = [module.application_insights]

  web_app_settings = {
    "WEBSITES_PORT"                       = "80"
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = "false"

    # Frontend environment variables - Supabase
    "VITE_SUPABASE_URL"     = module.supabase.api_url
    "VITE_SUPABASE_ANON_KEY" = var.supabase_anon_key != null ? var.supabase_anon_key : ""

    # URLs - constructed from name pattern (will match actual hostname)
    "VITE_SERVER_URL" = "https://${module.app_service.server_app_default_hostname}"
  }

  tags = local.common_tags
}

# ============================================================================
# Role-Based Access Control (RBAC) Assignments
# ============================================================================
module "rbac" {
  source = "./modules/rbac"

  key_vault_id                     = module.key_vault.id
  acr_id                           = module.acr.id
  server_app_identity_principal_id = module.app_service.server_app_identity_principal_id
  web_app_identity_principal_id    = module.app_service.web_app_identity_principal_id
  storage_account_id               = module.storage.storage_account_id
  ai_foundry_cognitive_account_id  = module.ai.ai_foundry_hub_id

  depends_on = [
    module.key_vault,
    module.acr,
    module.app_service,
    module.storage,
    module.ai
  ]
}


