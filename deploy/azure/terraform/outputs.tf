# ============================================================================
# Resource Group
# ============================================================================
output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

# ============================================================================
# Storage
# ============================================================================
output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.main.name
}

output "storage_account_key" {
  description = "Primary access key for the storage account"
  value       = azurerm_storage_account.main.primary_access_key
  sensitive   = true
}

output "storage_connection_string" {
  description = "Connection string for the storage account"
  value       = azurerm_storage_account.main.primary_connection_string
  sensitive   = true
}

output "input_container_name" {
  description = "Name of the input container"
  value       = azurerm_storage_container.input.name
}

output "output_container_name" {
  description = "Name of the output container"
  value       = azurerm_storage_container.output.name
}

output "ai_generation_tasks_queue_name" {
  description = "Name of the AI generation tasks storage queue"
  value       = azurerm_storage_queue.ai_generation_tasks.name
}

output "storage_account_identity_principal_id" {
  description = "Principal ID of the storage account managed identity"
  value       = azurerm_storage_account.main.identity[0].principal_id
}

# ============================================================================
# Azure AI Foundry
# ============================================================================
output "ai_foundry_endpoint" {
  description = "Azure AI Foundry endpoint"
  value       = azapi_resource.ai_foundry_account.output.properties.endpoint
}

output "ai_foundry_api_key" {
  description = "Azure AI Foundry API key"
  value       = data.azurerm_cognitive_account.ai_foundry_keys.primary_access_key
  sensitive   = true
}

output "gpt4o_deployment_name" {
  description = "Name of the GPT-4o deployment"
  value       = azapi_resource.model_deployments["gpt4o"].name
}

output "text_embedding_3_large_deployment_name" {
  description = "Name of the text-embedding-3-large deployment"
  value       = azapi_resource.model_deployments["text-embedding-3-large"].name
}

# ============================================================================
# Container Registry
# ============================================================================
output "acr_name" {
  description = "Name of the Azure Container Registry"
  value       = azurerm_container_registry.acr.name
}

output "acr_repository_api" {
  description = "ACR repository name for API"
  value       = var.acr_repository_api
}

output "acr_repository_worker" {
  description = "ACR repository name for worker"
  value       = var.acr_repository_worker
}

output "acr_repository_web" {
  description = "ACR repository name for web"
  value       = var.acr_repository_web
}

output "acr_webhooks_configured" {
  description = "Whether ACR webhooks are configured for auto-deployment"
  value       = length(azurerm_container_registry_webhook.deployment_webhooks) > 0
}

# ============================================================================
# Container Apps
# ============================================================================
output "container_app_api_url" {
  description = "FQDN of the API container app"
  value       = replace(azurerm_container_app.api.latest_revision_fqdn, "--[a-z0-9]+\\.", ".")
}

output "container_app_worker_name" {
  description = "Name of the worker container app"
  value       = azurerm_container_app.worker.name
}

# ============================================================================
# App Service (Web)
# ============================================================================
output "app_web_url" {
  description = "URL of the web app"
  value       = azurerm_linux_web_app.web.default_hostname
}

# ============================================================================
# Azure Tenant ID
# ============================================================================
output "azure_tenant_id" {
  description = "Azure Tenant ID"
  value       = var.azure_tenant_id
}

# ============================================================================
# Key Vault
# ============================================================================
output "azure_key_vault_uri" {
  description = "URI of the Azure Key Vault"
  value       = azurerm_key_vault.main.vault_uri
}

# ============================================================================
# Supabase
# ============================================================================
output "supabase_project_id" {
  description = "Supabase project ID"
  value       = supabase_project.main.id
}

output "supabase_project_ref" {
  description = "Supabase project reference ID"
  value       = supabase_project.main.id
}

output "supabase_api_url" {
  description = "Supabase API URL"
  value       = "https://${supabase_project.main.id}.supabase.co"
}

output "supabase_database_host" {
  description = "Supabase database host"
  value       = "db.${supabase_project.main.id}.supabase.co"
}

output "supabase_database_name" {
  description = "Supabase database name"
  value       = "postgres"
}

