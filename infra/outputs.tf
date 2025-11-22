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

output "documents_container_name" {
  description = "Name of the documents container"
  value       = module.storage.container_name
}

output "storage_account_identity_principal_id" {
  description = "Principal ID of the storage account managed identity"
  value       = module.storage.identity_principal_id
}

# Azure AI Foundry
output "ai_foundry_endpoint" {
  description = "Azure AI Foundry project endpoint"
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

# AI Services
output "ai_service_endpoint" {
  description = "AI Services endpoint"
  value       = module.ai.ai_service_endpoint
}

output "ai_service_key" {
  description = "AI Services API key"
  value       = module.ai.ai_service_key
  sensitive   = true
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

# App Services
output "app_server_url" {
  description = "URL of the server web app"
  value       = module.app_service.server_app_default_hostname
}

output "app_web_url" {
  description = "URL of the web app"
  value       = module.app_service.web_app_default_hostname
}

output "server_app_name" {
  description = "Name of the server app service"
  value       = module.app_service.server_app_name
}

output "web_app_name" {
  description = "Name of the web app service"
  value       = module.app_service.web_app_name
}

# Azure Entra ID
output "azure_tenant_id" {
  description = "Azure Tenant ID"
  value       = var.azure_tenant_id
}

output "azure_app_client_id" {
  description = "Azure App Client ID"
  value       = var.azure_app_client_id
}
