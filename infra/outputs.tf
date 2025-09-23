output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

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

output "documents_container_name" {
  description = "Name of the documents container"
  value       = azurerm_storage_container.documents.name
}

output "openai_endpoint" {
  description = "Azure OpenAI endpoint"
  value       = azurerm_cognitive_account.openai.endpoint
}

output "openai_api_key" {
  description = "Azure OpenAI API key"
  value       = azurerm_cognitive_account.openai.primary_access_key
  sensitive   = true
}

output "gpt4o_mini_deployment_name" {
  description = "Name of the GPT-4o Mini deployment"
  value       = azurerm_cognitive_deployment.gpt4o_mini.name
}

output "text_embedding_deployment_name" {
  description = "Name of the text embedding deployment"
  value       = azurerm_cognitive_deployment.text_embedding.name
}

output "search_service_name" {
  description = "Name of the Azure AI Search service"
  value       = azurerm_search_service.main.name
}

output "search_service_endpoint" {
  description = "Endpoint of the Azure AI Search service"
  value       = "https://${azurerm_search_service.main.name}.search.windows.net"
}

output "search_service_admin_key" {
  description = "Admin key for the Azure AI Search service"
  value       = azurerm_search_service.main.primary_key
  sensitive   = true
}

output "search_service_query_key" {
  description = "Query key for the Azure AI Search service"
  value       = azurerm_search_service.main.secondary_key
  sensitive   = true
}

output "document_intelligence_endpoint" {
  description = "Endpoint of the Azure AI Document Intelligence service"
  value       = azurerm_cognitive_account.document_intelligence.endpoint
}

output "document_intelligence_key" {
  description = "Key for the Azure AI Document Intelligence service"
  value       = azurerm_cognitive_account.document_intelligence.primary_access_key
  sensitive   = true
}
