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

output "gpt4o_deployment_name" {
  description = "Name of the GPT-4o deployment"
  value       = azurerm_cognitive_deployment.gpt4o.name
}

output "gpt4o_mini_deployment_name" {
  description = "Name of the GPT-4o Mini deployment"
  value       = azurerm_cognitive_deployment.gpt4o_mini.name
}

output "text_embedding_3_large_deployment_name" {
  description = "Name of the text-embedding-3-large deployment"
  value       = azurerm_cognitive_deployment.text_embedding_3_large.name
}

output "text_embedding_3_small_deployment_name" {
  description = "Name of the text-embedding-3-small deployment"
  value       = azurerm_cognitive_deployment.text_embedding_3_small.name
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

output "storage_account_identity_principal_id" {
  description = "Principal ID of the storage account managed identity"
  value       = azurerm_storage_account.main.identity[0].principal_id
}
