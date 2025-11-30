variable "key_vault_id" {
  description = "ID of the Azure Key Vault"
  type        = string
}

variable "acr_id" {
  description = "ID of the Azure Container Registry"
  type        = string
}

variable "server_app_identity_principal_id" {
  description = "Principal ID of the server app managed identity"
  type        = string
}

variable "web_app_identity_principal_id" {
  description = "Principal ID of the web app managed identity"
  type        = string
}

variable "storage_account_id" {
  description = "ID of the storage account"
  type        = string
}

variable "ai_foundry_cognitive_account_id" {
  description = "ID of the AI Foundry cognitive account (for OpenAI deployments)"
  type        = string
}

