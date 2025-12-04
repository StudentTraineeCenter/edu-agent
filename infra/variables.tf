# ============================================================================
# Azure Authentication & Identity
# ============================================================================
variable "azure_subscription_id" {
  description = "Azure Subscription ID"
  type        = string
}

variable "azure_tenant_id" {
  description = "Azure Tenant ID"
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
  description = "Database connection URL (stored in Key Vault). If using Supabase, this will be automatically generated from Supabase connection string."
  type        = string
  sensitive   = true
  default     = null
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

# ============================================================================
# Supabase Configuration
# ============================================================================
variable "supabase_access_token" {
  description = "Supabase Personal Access Token (from Dashboard > Account > Access Tokens)"
  type        = string
  sensitive   = true
}

variable "supabase_organization_id" {
  description = "Supabase Organization ID"
  type        = string
  sensitive   = true
}

variable "supabase_database_password" {
  description = "Database password for Supabase project"
  type        = string
  sensitive   = true
}

variable "supabase_region" {
  description = "AWS region for Supabase project (e.g., 'us-east-1', 'eu-west-1', 'ap-southeast-1')"
  type        = string
  default     = "eu-central-2"
}

variable "supabase_service_role_key" {
  description = "Supabase service role key (from Dashboard > Project Settings > API > service_role secret)"
  type        = string
  sensitive   = true
  default     = null
}

variable "supabase_jwt_secret" {
  description = "Supabase JWT secret (from Dashboard > Project Settings > Auth > JWT Settings)"
  type        = string
  sensitive   = true
  default     = null
}

variable "supabase_anon_key" {
  description = "Supabase anonymous key (from Dashboard > Project Settings > API > anon public key)"
  type        = string
  sensitive   = true
  default     = null
}
