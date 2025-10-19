variable "azure_subscription_id" {
  description = "Azure Subscription ID"
  type        = string
}

variable "azure_tenant_id" {
  description = "Azure Tenant ID"
  type        = string
}

variable "azure_app_client_id" {
  description = "Azure App Client ID"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "rg-edu-agent"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "Sweden Central"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "edu-agent"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "acr_repository_api" {
  type    = string
  default = "edu-agent-api"
}

variable "acr_tag_api" {
  type    = string
  default = "latest"
}

variable "acr_repository_web" {
  type    = string
  default = "edu-agent-web"
}

variable "acr_tag_web" {
  type    = string
  default = "latest"
}

# Database variables (DISABLED - PostgreSQL disabled)
# variable "database_admin_username" {
#   description = "Username for the database admin"
#   type        = string
#   default     = "postgres"
# }

# variable "database_admin_password" {
#   description = "Password for the database admin"
#   type        = string
#   default     = "postgres"
# }
