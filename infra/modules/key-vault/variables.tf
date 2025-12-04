variable "key_vault_name" {
  description = "Name of the Key Vault"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region for resources"
  type        = string
}

variable "sku_name" {
  description = "SKU name for the Key Vault"
  type        = string
  default     = "standard"
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}


# Secret values to store in Key Vault
variable "database_url" {
  description = "Database connection URL"
  type        = string
  default     = null
  sensitive   = true
}

variable "azure_storage_connection_string" {
  description = "Azure Storage connection string"
  type        = string
  default     = null
  sensitive   = true
}

variable "azure_storage_input_container_name" {
  description = "Azure Storage input container name"
  type        = string
  default     = null
}

variable "azure_storage_output_container_name" {
  description = "Azure Storage output container name"
  type        = string
  default     = null
}

# Note: AI-related secret variables removed - these secrets are created in main.tf
# after the AI module is created to avoid circular dependencies


