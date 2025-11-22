output "ai_foundry_endpoint" {
  description = "Azure AI Foundry OpenAI endpoint"
  value       = azurerm_cognitive_account.openai.endpoint
}

output "ai_foundry_api_key" {
  description = "Azure AI Foundry OpenAI API key"
  value       = azurerm_cognitive_account.openai.primary_access_key
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

output "ai_foundry_project_id" {
  description = "ID of the AI Foundry project"
  value       = azurerm_ai_foundry_project.project.id
}

output "ai_foundry_hub_id" {
  description = "ID of the AI Foundry hub"
  value       = azurerm_ai_foundry.hub.id
}

