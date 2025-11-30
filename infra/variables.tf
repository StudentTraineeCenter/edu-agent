# Azure Authentication
variable "azure_subscription_id" {
  description = "Azure Subscription ID"
  type        = string
}

variable "azure_tenant_id" {
  description = "Azure Tenant ID"
  type        = string
}

variable "database_url" {
  description = "Database connection URL"
  type        = string
}

variable "azure_app_client_id" {
  description = "Azure App Client ID"
  type        = string
}

# Infrastructure Configuration
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

variable "region_code" {
  description = "Short region code for CAF naming (e.g., swc for Sweden Central)"
  type        = string
  default     = "swc"
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

variable "workload" {
  description = "Workload name for CAF naming (optional)"
  type        = string
  default     = ""
}

# Container Registry Configuration
variable "acr_repository_server" {
  description = "ACR repository name for server"
  type        = string
  default     = "edu-agent-server"
}

variable "acr_tag_server" {
  description = "ACR tag for server"
  type        = string
  default     = "latest"
}

variable "acr_repository_web" {
  description = "ACR repository name for web"
  type        = string
  default     = "edu-agent-web"
}

variable "acr_tag_web" {
  description = "ACR tag for web"
  type        = string
  default     = "latest"
}

# Database Configuration (DISABLED)
# Uncomment these when enabling the database module
# variable "database_admin_username" {
#   description = "Username for the database admin"
#   type        = string
#   default     = "postgres"
# }
#
# variable "database_admin_password" {
#   description = "Password for the database admin"
#   type        = string
#   sensitive   = true
# }
