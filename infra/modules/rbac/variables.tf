variable "acr_id" {
  description = "ID of the Azure Container Registry"
  type        = string
}

variable "api_app_identity_principal_id" {
  description = "Principal ID of the API app managed identity"
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

variable "ai_foundry_project_id" {
  description = "ID of the AI Foundry project"
  type        = string
}

