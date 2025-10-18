variable "azure_subscription_id" {
  description = "Azure Subscription ID"
  type        = string
  default     = "a5baa9fd-933f-47a1-8175-da59a43170bb"
}

variable "azure_tenant_id" {
  description = "Azure Tenant ID"
  type        = string
  default     = "45ab8ba3-4ca1-45bd-95d7-18658bb01287"
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
