variable "location" {
  description = "Azure region for resources"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
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
  description = "SKU capacity for GPT-4o deployment in thousands (e.g., 1 = 1,000 tokens/minute). Must be a positive integer."
  type        = number
  default     = 50

  validation {
    condition     = var.gpt4o_sku_capacity > 0 && var.gpt4o_sku_capacity == floor(var.gpt4o_sku_capacity)
    error_message = "GPT-4o SKU capacity must be a positive integer."
  }
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
  description = "SKU capacity for text embedding deployment in thousands (e.g., 1 = 1,000 tokens/minute). Must be a positive integer."
  type        = number
  default     = 500

  validation {
    condition     = var.text_embedding_sku_capacity > 0 && var.text_embedding_sku_capacity == floor(var.text_embedding_sku_capacity)
    error_message = "Text embedding SKU capacity must be a positive integer."
  }
}

variable "ai_foundry_hub_name" {
  description = "Name of the AI Foundry hub (cognitive account)"
  type        = string
}

variable "ai_foundry_project_name" {
  description = "Name of the AI Foundry project"
  type        = string
  default     = "default-project"
}

variable "storage_account_id" {
  description = "ID of the storage account for AI Foundry (optional, for future use)"
  type        = string
  default     = null
}

variable "key_vault_id" {
  description = "ID of the key vault for AI Foundry (optional, for future use)"
  type        = string
  default     = null
}


variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

