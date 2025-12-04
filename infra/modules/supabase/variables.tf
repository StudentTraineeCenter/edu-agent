variable "supabase_organization_id" {
  description = "Supabase Organization ID"
  type        = string
  sensitive   = true
}

variable "project_name" {
  description = "Name of the Supabase project"
  type        = string
}

variable "database_password" {
  description = "Database password for Supabase project"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "AWS region for Supabase project (e.g., 'us-east-1', 'eu-west-1', 'ap-southeast-1')"
  type        = string
  default     = "eu-central-2"
}

variable "site_url" {
  description = "Site URL for authentication redirects"
  type        = string
}

