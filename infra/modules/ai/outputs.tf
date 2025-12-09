# ============================================================================
# AI Foundry Account Outputs
# ============================================================================
output "ai_foundry_endpoint" {
  description = "Azure AI Foundry cognitive account endpoint for model deployments"
  value       = local.ai_foundry_endpoint
}

output "ai_foundry_subdomain" {
  description = "Azure AI Foundry cognitive account custom subdomain"
  value       = var.ai_foundry_hub_name
}

output "ai_foundry_api_key" {
  description = "Azure AI Foundry cognitive account API key for model deployments"
  value       = data.azurerm_cognitive_account.ai_foundry_keys.primary_access_key
  sensitive   = true
  # Note: For production, prefer managed identity authentication over API keys
}

output "ai_foundry_hub_id" {
  description = "ID of the AI Foundry cognitive account (acts as hub)"
  value       = azapi_resource.ai_foundry_account.id
}

output "ai_foundry_account_principal_id" {
  description = "Principal ID of the Foundry account managed identity"
  value       = local.ai_foundry_account_principal_id
}

# ============================================================================
# AI Foundry Project Outputs
# ============================================================================
output "ai_foundry_project_name" {
  description = "Name of the Azure AI Foundry project"
  value       = azapi_resource.ai_foundry_project.name
}

output "ai_foundry_project_endpoint" {
  description = "The API endpoint for the Azure AI Foundry project"
  value       = local.ai_foundry_project_endpoint
}

output "ai_foundry_project_principal_id" {
  description = "Principal ID of the Foundry project managed identity"
  value       = local.ai_foundry_project_principal_id
}

# ============================================================================
# Model Deployment Outputs
# ============================================================================
output "gpt4o_deployment_name" {
  description = "Name of the GPT-4o deployment"
  value       = azapi_resource.model_deployments["gpt4o"].name
}

output "text_embedding_3_large_deployment_name" {
  description = "Name of the text-embedding-3-large deployment"
  value       = azapi_resource.model_deployments["text-embedding-3-large"].name
}

# ============================================================================
# OpenAI Endpoint Outputs
# ============================================================================
output "azure_openai_endpoint" {
  description = "The Azure OpenAI endpoint for chat completions"
  value       = local.azure_openai_endpoint
}


