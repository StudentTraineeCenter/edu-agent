output "service_plan_id" {
  description = "ID of the App Service Plan"
  value       = azurerm_service_plan.web.id
}

output "server_app_id" {
  description = "ID of the server web app"
  value       = azurerm_linux_web_app.server.id
}

output "server_app_name" {
  description = "Name of the server web app"
  value       = azurerm_linux_web_app.server.name
}

output "server_app_default_hostname" {
  description = "Default hostname of the server web app"
  value       = azurerm_linux_web_app.server.default_hostname
}

output "server_app_identity_principal_id" {
  description = "Principal ID of the server app managed identity"
  value       = azurerm_linux_web_app.server.identity[0].principal_id
}

output "web_app_id" {
  description = "ID of the web app"
  value       = azurerm_linux_web_app.web.id
}

output "web_app_name" {
  description = "Name of the web app"
  value       = azurerm_linux_web_app.web.name
}

output "web_app_default_hostname" {
  description = "Default hostname of the web app"
  value       = azurerm_linux_web_app.web.default_hostname
}

output "web_app_identity_principal_id" {
  description = "Principal ID of the web app managed identity"
  value       = azurerm_linux_web_app.web.identity[0].principal_id
}

