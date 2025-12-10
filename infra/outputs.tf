# Resource Group
output "resource_group_name" {
  description = "Name of the resource group"
  value       = module.resource_group.name
}

# Storage
output "storage_account_name" {
  description = "Name of the storage account"
  value       = module.storage.storage_account_name
}

output "storage_account_key" {
  description = "Primary access key for the storage account"
  value       = module.storage.primary_access_key
  sensitive   = true
}

output "storage_connection_string" {
  description = "Connection string for the storage account"
  value       = module.storage.primary_connection_string
  sensitive   = true
}

output "input_container_name" {
  description = "Name of the input container"
  value       = module.storage.input_container_name
}

output "output_container_name" {
  description = "Name of the output container"
  value       = module.storage.output_container_name
}

output "storage_account_identity_principal_id" {
  description = "Principal ID of the storage account managed identity"
  value       = module.storage.identity_principal_id
}

# Azure AI Foundry
output "ai_foundry_endpoint" {
  description = "Azure AI Foundry endpoint"
  value       = module.ai.ai_foundry_endpoint
}

output "ai_foundry_api_key" {
  description = "Azure AI Foundry API key"
  value       = module.ai.ai_foundry_api_key
  sensitive   = true
}

output "gpt4o_deployment_name" {
  description = "Name of the GPT-4o deployment"
  value       = module.ai.gpt4o_deployment_name
}

output "text_embedding_3_large_deployment_name" {
  description = "Name of the text-embedding-3-large deployment"
  value       = module.ai.text_embedding_3_large_deployment_name
}

# Container Registry
output "acr_name" {
  description = "Name of the Azure Container Registry"
  value       = module.acr.name
}

output "acr_repository_server" {
  description = "ACR repository name for server"
  value       = var.acr_repository_server
}

output "acr_repository_web" {
  description = "ACR repository name for web"
  value       = var.acr_repository_web
}

output "acr_webhooks_configured" {
  description = "Whether ACR webhooks are configured for auto-deployment"
  value       = length(azurerm_container_registry_webhook.deployment_webhooks) > 0
}

# Container App (Server)
output "container_app_server_url" {
  description = "FQDN of the server container app"
  value       = module.container_app.app_fqdn
}

# App Service (Web)
output "app_web_url" {
  description = "URL of the web app"
  value       = module.app_service.web_app_default_hostname
}

# Azure Tenant ID
output "azure_tenant_id" {
  description = "Azure Tenant ID"
  value       = var.azure_tenant_id
}

# Key Vault
output "azure_key_vault_uri" {
  description = "URI of the Azure Key Vault"
  value       = module.key_vault.uri
}

# Supabase
output "supabase_project_id" {
  description = "Supabase project ID"
  value       = module.supabase.project_id
}

output "supabase_project_ref" {
  description = "Supabase project reference ID"
  value       = module.supabase.project_ref
}

output "supabase_api_url" {
  description = "Supabase API URL"
  value       = module.supabase.api_url
}

output "supabase_database_host" {
  description = "Supabase database host"
  value       = module.supabase.database_host
}

output "supabase_database_name" {
  description = "Supabase database name"
  value       = module.supabase.database_name
}
