# ============================================================================
# Azure Authentication & Identity
# ============================================================================
variable "azure_subscription_id" {
  description = "Azure Subscription ID"
  type        = string
}

variable "azure_tenant_id" {
  description = "Azure Entra ID (formerly Azure AD) Tenant ID"
  type        = string
}

variable "azure_app_client_id" {
  description = "Azure Entra ID Application (Client) ID for authentication"
  type        = string
}

# ============================================================================
# Infrastructure Configuration
# ============================================================================
variable "location" {
  description = "Azure region for resources (e.g., 'Sweden Central')"
  type        = string
  default     = "Sweden Central"
}

variable "region_code" {
  description = "Short region code for CAF naming convention (e.g., 'swc' for Sweden Central)"
  type        = string
  default     = "swc"
}

variable "project_name" {
  description = "Project name used in CAF naming convention"
  type        = string
  default     = "edu-agent"
}

variable "environment" {
  description = "Environment name (dev, staging, prod). Used in CAF naming convention."
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "workload" {
  description = "Optional workload name for CAF naming convention (e.g., 'api', 'web')"
  type        = string
  default     = ""
}

# ============================================================================
# Application Configuration
# ============================================================================
variable "database_url" {
  description = "Database connection URL (stored in Key Vault)"
  type        = string
  sensitive   = true
}

# ============================================================================
# Container Registry Configuration
# ============================================================================
variable "acr_repository_server" {
  description = "Azure Container Registry repository name for server application"
  type        = string
  default     = "edu-agent-server"
}

variable "acr_tag_server" {
  description = "Container image tag for server application"
  type        = string
  default     = "latest"
}

variable "acr_repository_web" {
  description = "Azure Container Registry repository name for web application"
  type        = string
  default     = "edu-agent-web"
}

variable "acr_tag_web" {
  description = "Container image tag for web application"
  type        = string
  default     = "latest"
}
