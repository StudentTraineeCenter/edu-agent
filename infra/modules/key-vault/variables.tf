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

variable "azure_storage_container_name" {
  description = "Azure Storage container name"
  type        = string
  default     = null
}

variable "azure_openai_api_key" {
  description = "Azure OpenAI API key"
  type        = string
  default     = null
  sensitive   = true
}

variable "azure_openai_endpoint" {
  description = "Azure OpenAI endpoint"
  type        = string
  default     = null
}

variable "azure_openai_default_model" {
  description = "Azure OpenAI default model"
  type        = string
  default     = null
}

variable "azure_openai_embedding_deployment" {
  description = "Azure OpenAI embedding deployment name"
  type        = string
  default     = null
}

variable "azure_openai_chat_deployment" {
  description = "Azure OpenAI chat deployment name"
  type        = string
  default     = null
}

variable "azure_openai_api_version" {
  description = "Azure OpenAI API version"
  type        = string
  default     = null
}

variable "azure_document_intelligence_endpoint" {
  description = "Azure Document Intelligence endpoint"
  type        = string
  default     = null
}

variable "azure_document_intelligence_key" {
  description = "Azure Document Intelligence key"
  type        = string
  default     = null
  sensitive   = true
}

variable "azure_entra_tenant_id" {
  description = "Azure Entra ID tenant ID"
  type        = string
  default     = null
}

variable "azure_entra_client_id" {
  description = "Azure Entra ID client ID"
  type        = string
  default     = null
}

variable "azure_cu_endpoint" {
  description = "Azure Content Understanding endpoint"
  type        = string
  default     = null
}

variable "azure_cu_key" {
  description = "Azure Content Understanding key"
  type        = string
  default     = null
  sensitive   = true
}

variable "azure_cu_analyzer_id" {
  description = "Azure Content Understanding analyzer ID"
  type        = string
  default     = null
}

