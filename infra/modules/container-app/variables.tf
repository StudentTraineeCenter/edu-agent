variable "environment_name" {
  description = "Name of the Container App Environment"
  type        = string
}

variable "location" {
  description = "Azure region for resources"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "log_analytics_workspace_id" {
  description = "ID of the Log Analytics Workspace for Container App Environment"
  type        = string
}

variable "app_name" {
  description = "Name of the container app"
  type        = string
}

variable "acr_login_server" {
  description = "ACR login server URL"
  type        = string
}

variable "acr_id" {
  description = "ID of the Azure Container Registry"
  type        = string
}

variable "acr_repository" {
  description = "ACR repository name"
  type        = string
}

variable "acr_tag" {
  description = "ACR tag"
  type        = string
  default     = "latest"
}

variable "target_port" {
  description = "Target port for the container app"
  type        = number
  default     = 8000
}

variable "min_replicas" {
  description = "Minimum number of replicas"
  type        = number
  default     = 1
}

variable "max_replicas" {
  description = "Maximum number of replicas"
  type        = number
  default     = 10
}

variable "cpu" {
  description = "CPU allocation for each replica (e.g., 0.25, 0.5, 1.0, 1.25, 1.5, 1.75, 2.0)"
  type        = number
  default     = 0.5
}

variable "memory" {
  description = "Memory allocation for each replica (e.g., 0.5Gi, 1.0Gi, 2.0Gi)"
  type        = string
  default     = "1.0Gi"
}

variable "key_vault_uri" {
  description = "URI of the Azure Key Vault"
  type        = string
}

variable "app_insights_connection_string" {
  description = "Application Insights connection string"
  type        = string
}

variable "cors_allowed_origins" {
  description = "CORS allowed origins"
  type        = string
}

variable "max_chat_messages_per_day" {
  description = "Maximum chat messages per day"
  type        = string
  default     = "50"
}

variable "max_flashcard_generations_per_day" {
  description = "Maximum flashcard generations per day"
  type        = string
  default     = "10"
}

variable "max_quiz_generations_per_day" {
  description = "Maximum quiz generations per day"
  type        = string
  default     = "10"
}

variable "max_document_uploads_per_day" {
  description = "Maximum document uploads per day"
  type        = string
  default     = "5"
}

variable "additional_env_vars" {
  description = "Additional environment variables"
  type        = map(string)
  default     = {}
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
