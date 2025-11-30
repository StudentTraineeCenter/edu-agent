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

output "azure_entra_tenant_id_secret_uri" {
  description = "URI of the azure-entra-tenant-id secret"
  value       = try(azurerm_key_vault_secret.azure_entra_tenant_id[0].id, null)
}

output "azure_entra_client_id_secret_uri" {
  description = "URI of the azure-entra-client-id secret"
  value       = try(azurerm_key_vault_secret.azure_entra_client_id[0].id, null)
}

# Note: AI-related secret URIs are not output here as those secrets are created in main.tf
# after the AI module is created to avoid circular dependencies

