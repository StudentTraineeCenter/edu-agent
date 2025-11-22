output "id" {
  description = "ID of the Key Vault"
  value       = azurerm_key_vault.main.id
}

output "name" {
  description = "Name of the Key Vault"
  value       = azurerm_key_vault.main.name
}

output "uri" {
  description = "URI of the Key Vault"
  value       = azurerm_key_vault.main.vault_uri
}

# Secret URIs for reference in app settings
output "database_url_secret_uri" {
  description = "URI of the database-url secret"
  value       = try(azurerm_key_vault_secret.database_url[0].id, null)
}

output "azure_storage_connection_string_secret_uri" {
  description = "URI of the azure-storage-connection-string secret"
  value       = try(azurerm_key_vault_secret.azure_storage_connection_string[0].id, null)
}

output "azure_storage_container_name_secret_uri" {
  description = "URI of the azure-storage-container-name secret"
  value       = try(azurerm_key_vault_secret.azure_storage_container_name[0].id, null)
}

output "azure_openai_api_key_secret_uri" {
  description = "URI of the azure-openai-api-key secret"
  value       = try(azurerm_key_vault_secret.azure_openai_api_key[0].id, null)
}

output "azure_openai_endpoint_secret_uri" {
  description = "URI of the azure-openai-endpoint secret"
  value       = try(azurerm_key_vault_secret.azure_openai_endpoint[0].id, null)
}

output "azure_openai_default_model_secret_uri" {
  description = "URI of the azure-openai-default-model secret"
  value       = try(azurerm_key_vault_secret.azure_openai_default_model[0].id, null)
}

output "azure_openai_embedding_deployment_secret_uri" {
  description = "URI of the azure-openai-embedding-deployment secret"
  value       = try(azurerm_key_vault_secret.azure_openai_embedding_deployment[0].id, null)
}

output "azure_openai_chat_deployment_secret_uri" {
  description = "URI of the azure-openai-chat-deployment secret"
  value       = try(azurerm_key_vault_secret.azure_openai_chat_deployment[0].id, null)
}

output "azure_openai_api_version_secret_uri" {
  description = "URI of the azure-openai-api-version secret"
  value       = try(azurerm_key_vault_secret.azure_openai_api_version[0].id, null)
}

output "azure_document_intelligence_endpoint_secret_uri" {
  description = "URI of the azure-document-intelligence-endpoint secret"
  value       = try(azurerm_key_vault_secret.azure_document_intelligence_endpoint[0].id, null)
}

output "azure_document_intelligence_key_secret_uri" {
  description = "URI of the azure-document-intelligence-key secret"
  value       = try(azurerm_key_vault_secret.azure_document_intelligence_key[0].id, null)
}

output "azure_entra_tenant_id_secret_uri" {
  description = "URI of the azure-entra-tenant-id secret"
  value       = try(azurerm_key_vault_secret.azure_entra_tenant_id[0].id, null)
}

output "azure_entra_client_id_secret_uri" {
  description = "URI of the azure-entra-client-id secret"
  value       = try(azurerm_key_vault_secret.azure_entra_client_id[0].id, null)
}

output "azure_cu_endpoint_secret_uri" {
  description = "URI of the azure-cu-endpoint secret"
  value       = try(azurerm_key_vault_secret.azure_cu_endpoint[0].id, null)
}

output "azure_cu_key_secret_uri" {
  description = "URI of the azure-cu-key secret"
  value       = try(azurerm_key_vault_secret.azure_cu_key[0].id, null)
}

output "azure_cu_analyzer_id_secret_uri" {
  description = "URI of the azure-cu-analyzer-id secret"
  value       = try(azurerm_key_vault_secret.azure_cu_analyzer_id[0].id, null)
}

