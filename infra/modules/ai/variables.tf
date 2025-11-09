variable "location" {
  description = "Azure region for resources"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "openai_account_name" {
  description = "Name of the OpenAI cognitive account"
  type        = string
}

variable "openai_sku_name" {
  description = "SKU name for OpenAI account"
  type        = string
  default     = "S0"
}

variable "openai_custom_subdomain_name" {
  description = "Custom subdomain name for OpenAI"
  type        = string
}

variable "gpt4o_deployment_name" {
  description = "Name of the GPT-4o deployment"
  type        = string
  default     = "gpt-4o"
}

variable "gpt4o_model_name" {
  description = "Model name for GPT-4o"
  type        = string
  default    = "gpt-4o"
}

variable "gpt4o_model_version" {
  description = "Model version for GPT-4o"
  type        = string
  default     = "2024-11-20"
}

variable "gpt4o_sku_name" {
  description = "SKU name for GPT-4o deployment"
  type        = string
  default     = "GlobalStandard"
}

variable "gpt4o_sku_capacity" {
  description = "SKU capacity for GPT-4o deployment"
  type        = number
  default     = 1
}

variable "text_embedding_deployment_name" {
  description = "Name of the text embedding deployment"
  type        = string
  default     = "text-embedding-3-large"
}

variable "text_embedding_model_name" {
  description = "Model name for text embedding"
  type        = string
  default     = "text-embedding-3-large"
}

variable "text_embedding_model_version" {
  description = "Model version for text embedding"
  type        = string
  default     = "1"
}

variable "text_embedding_sku_name" {
  description = "SKU name for text embedding deployment"
  type        = string
  default     = "GlobalStandard"
}

variable "text_embedding_sku_capacity" {
  description = "SKU capacity for text embedding deployment"
  type        = number
  default     = 1
}

variable "ai_foundry_hub_name" {
  description = "Name of the AI Foundry hub"
  type        = string
}

variable "ai_foundry_project_name" {
  description = "Name of the AI Foundry project"
  type        = string
}

variable "storage_account_id" {
  description = "ID of the storage account for AI Foundry"
  type        = string
}

variable "key_vault_id" {
  description = "ID of the key vault for AI Foundry"
  type        = string
}

variable "ai_services_name" {
  description = "Name of the AI Services resource"
  type        = string
}

variable "ai_services_sku_name" {
  description = "SKU name for AI Services"
  type        = string
  default     = "S0"
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

