output "storage_account_id" {
  description = "ID of the storage account"
  value       = azurerm_storage_account.main.id
}

output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.main.name
}

output "primary_access_key" {
  description = "Primary access key for the storage account (deprecated - use RBAC with managed identity instead)"
  value       = azurerm_storage_account.main.primary_access_key
  sensitive   = true
}

output "primary_connection_string" {
  description = "Primary connection string for the storage account (deprecated - use RBAC with managed identity instead). Only stored in Key Vault for backward compatibility."
  value       = azurerm_storage_account.main.primary_connection_string
  sensitive   = true
}

output "identity_principal_id" {
  description = "Principal ID of the storage account managed identity"
  value       = azurerm_storage_account.main.identity[0].principal_id
}

output "container_name" {
  description = "Name of the storage container"
  value       = azurerm_storage_container.documents.name
}

