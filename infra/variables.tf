variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "rg-edu-agent"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "West Europe"
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

variable "database_admin_username" {
  description = "Username for the database admin"
  type        = string
  default     = "postgres"
}

variable "database_admin_password" {
  description = "Password for the database admin"
  type        = string
  default     = "postgres"
}