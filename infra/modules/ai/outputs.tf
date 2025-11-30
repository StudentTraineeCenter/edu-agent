output "ai_foundry_endpoint" {
  description = "Azure AI Foundry cognitive account endpoint for model deployments"
  value       = azurerm_cognitive_account.ai_foundry.endpoint
}

output "ai_foundry_subdomain" {
  description = "Azure AI Foundry cognitive account custom subdomain"
  value       = azurerm_cognitive_account.ai_foundry.custom_subdomain_name
}

output "ai_foundry_api_key" {
  description = "Azure AI Foundry cognitive account API key for model deployments"
  value       = azurerm_cognitive_account.ai_foundry.primary_access_key
  sensitive   = true
}

output "gpt4o_deployment_name" {
  description = "Name of the GPT-4o deployment"
  value       = azurerm_cognitive_deployment.gpt4o.name
}

output "text_embedding_3_large_deployment_name" {
  description = "Name of the text-embedding-3-large deployment"
  value       = azurerm_cognitive_deployment.text_embedding_3_large.name
}

output "ai_service_endpoint" {
  description = "AI Services endpoint"
  value       = azurerm_ai_services.service.endpoint
}

output "ai_service_key" {
  description = "AI Services API key"
  value       = azurerm_ai_services.service.primary_access_key
  sensitive   = true
}

output "ai_foundry_hub_id" {
  description = "ID of the AI Foundry cognitive account (acts as hub)"
  value       = azurerm_cognitive_account.ai_foundry.id
}

