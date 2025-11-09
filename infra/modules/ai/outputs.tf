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

output "openai_account_id" {
  description = "ID of the OpenAI cognitive account"
  value       = azurerm_cognitive_account.openai.id
}

