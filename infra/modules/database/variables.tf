variable "server_name" {
  description = "Name of the PostgreSQL flexible server"
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

variable "postgres_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "16"
}

variable "administrator_login" {
  description = "Username for the database administrator"
  type        = string
  sensitive   = true
}

variable "administrator_password" {
  description = "Password for the database administrator"
  type        = string
  sensitive   = true
}

variable "storage_mb" {
  description = "Storage size in MB"
  type        = number
  default     = 32768
}

variable "storage_tier" {
  description = "Storage tier"
  type        = string
  default     = "P4"
}

variable "sku_name" {
  description = "SKU name for the PostgreSQL server"
  type        = string
  default     = "B_Standard_B1ms"
}

variable "auto_grow_enabled" {
  description = "Enable auto-grow for storage"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Backup retention days"
  type        = number
  default     = 7
}

variable "geo_redundant_backup_enabled" {
  description = "Enable geo-redundant backup"
  type        = bool
  default     = false
}

variable "database_name" {
  description = "Name of the PostgreSQL database"
  type        = string
}

variable "database_collation" {
  description = "Database collation"
  type        = string
  default     = "en_US.utf8"
}

variable "database_charset" {
  description = "Database charset"
  type        = string
  default     = "utf8"
}

variable "firewall_rule_name" {
  description = "Name of the firewall rule for Azure services"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

