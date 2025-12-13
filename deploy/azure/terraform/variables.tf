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
variable "acr_repository_api" {
  description = "Azure Container Registry repository name for API application"
  type        = string
  default     = "edu-api"
}

variable "acr_tag_api" {
  description = "Container image tag for API application"
  type        = string
  default     = "latest"
}

variable "acr_repository_worker" {
  description = "Azure Container Registry repository name for worker application"
  type        = string
  default     = "edu-worker"
}

variable "acr_tag_worker" {
  description = "Container image tag for worker application"
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
  default     = "eu-north-1"
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

# ============================================================================
# AI Configuration
# ============================================================================
variable "gpt4o_deployment_name" {
  description = "Name of the GPT-4o deployment"
  type        = string
  default     = "gpt-4o"
}

variable "gpt4o_model_name" {
  description = "Model name for GPT-4o"
  type        = string
  default     = "gpt-4o"
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
  description = "SKU capacity for GPT-4o deployment in thousands (e.g., 1 = 1,000 tokens/minute). Must be a positive integer. Reduce if quota is insufficient."
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
  default     = 100

  validation {
    condition     = var.text_embedding_sku_capacity > 0 && var.text_embedding_sku_capacity == floor(var.text_embedding_sku_capacity)
    error_message = "Text embedding SKU capacity must be a positive integer."
  }
}

# ============================================================================
# Container App Configuration - API
# ============================================================================
variable "api_target_port" {
  description = "Target port for the API container app"
  type        = number
  default     = 8000
}

variable "api_min_replicas" {
  description = "Minimum number of replicas for API"
  type        = number
  default     = 1
}

variable "api_max_replicas" {
  description = "Maximum number of replicas for API"
  type        = number
  default     = 10
}

variable "api_cpu" {
  description = "CPU allocation for each API replica (e.g., 0.25, 0.5, 1.0, 1.25, 1.5, 1.75, 2.0)"
  type        = number
  default     = 0.5
}

variable "api_memory" {
  description = "Memory allocation for each API replica (e.g., 0.5Gi, 1.0Gi, 2.0Gi)"
  type        = string
  default     = "1.0Gi"
}

variable "api_additional_env_vars" {
  description = "Additional environment variables for API container app"
  type        = map(string)
  default     = {}
}

# ============================================================================
# Container App Configuration - Worker
# ============================================================================
variable "worker_min_replicas" {
  description = "Minimum number of replicas for worker"
  type        = number
  default     = 1
}

variable "worker_max_replicas" {
  description = "Maximum number of replicas for worker"
  type        = number
  default     = 10
}

variable "worker_cpu" {
  description = "CPU allocation for each worker replica (e.g., 0.25, 0.5, 1.0, 1.25, 1.5, 1.75, 2.0)"
  type        = number
  default     = 0.5
}

variable "worker_memory" {
  description = "Memory allocation for each worker replica (e.g., 0.5Gi, 1.0Gi, 2.0Gi)"
  type        = string
  default     = "1.0Gi"
}

variable "worker_additional_env_vars" {
  description = "Additional environment variables for worker container app"
  type        = map(string)
  default     = {}
}

# ============================================================================
# Application Limits
# ============================================================================
variable "max_chat_messages_per_day" {
  description = "Maximum chat messages per day"
  type        = string
  default     = "50"
}

variable "max_flashcard_generations_per_day" {
  description = "Maximum flashcard generations per day"
  type        = string
  default     = "10"
}

variable "max_quiz_generations_per_day" {
  description = "Maximum quiz generations per day"
  type        = string
  default     = "10"
}

variable "max_document_uploads_per_day" {
  description = "Maximum document uploads per day"
  type        = string
  default     = "5"
}

# ============================================================================
# App Service Configuration
# ============================================================================
variable "app_service_os_type" {
  description = "OS type for the App Service Plan"
  type        = string
  default     = "Linux"
}

variable "app_service_sku_name" {
  description = "SKU name for the App Service Plan"
  type        = string
  default     = "B1"
}

variable "web_health_check_path" {
  description = "Health check path for web app"
  type        = string
  default     = "/"
}

variable "health_check_eviction_time_in_min" {
  description = "Health check eviction time in minutes"
  type        = number
  default     = 10
}

