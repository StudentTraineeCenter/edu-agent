output "environment_id" {
  description = "ID of the Container App Environment"
  value       = azurerm_container_app_environment.main.id
}

output "environment_name" {
  description = "Name of the Container App Environment"
  value       = azurerm_container_app_environment.main.name
}

output "app_id" {
  description = "ID of the container app"
  value       = azurerm_container_app.server.id
}

output "app_name" {
  description = "Name of the container app"
  value       = azurerm_container_app.server.name
}

output "app_fqdn" {
  description = "FQDN of the container app"
  value       = azurerm_container_app.server.latest_revision_fqdn
}

output "app_identity_principal_id" {
  description = "Principal ID of the container app managed identity"
  value       = azurerm_user_assigned_identity.container_app.principal_id
}

output "app_identity_id" {
  description = "ID of the user-assigned managed identity"
  value       = azurerm_user_assigned_identity.container_app.id
}
