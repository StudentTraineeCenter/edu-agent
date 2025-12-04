output "project_id" {
  description = "Supabase project ID"
  value       = supabase_project.main.id
}

output "project_ref" {
  description = "Supabase project reference ID (same as project ID)"
  value       = supabase_project.main.id
}

output "api_url" {
  description = "Supabase API URL (constructed from project ID)"
  value       = "https://${supabase_project.main.id}.supabase.co"
}

# Note: The following outputs require manual configuration or API calls
# The Supabase Terraform provider doesn't expose these as resource attributes
# You'll need to retrieve them from the Supabase dashboard or API

output "anon_key" {
  description = "Supabase anonymous key - must be set manually or retrieved via API"
  value       = ""
  sensitive   = true
}

output "service_role_key" {
  description = "Supabase service role key - must be set manually or retrieved via API"
  value       = ""
  sensitive   = true
}

output "jwt_secret" {
  description = "Supabase JWT secret - must be retrieved from Supabase dashboard (Settings > API > JWT Settings)"
  value       = ""
  sensitive   = true
}

# Database connection info - Supabase uses standard patterns
output "database_host" {
  description = "Database host (constructed from project ID)"
  value       = "db.${supabase_project.main.id}.supabase.co"
}

output "database_name" {
  description = "Database name (default for Supabase)"
  value       = "postgres"
}

output "database_port" {
  description = "Database port (default for PostgreSQL)"
  value       = 5432
}

output "database_user" {
  description = "Database user (default for Supabase)"
  value       = "postgres"
}

output "database_connection_string" {
  description = "Full PostgreSQL connection string for Supabase database"
  # Construct PostgreSQL connection string using Supabase's standard pattern
  # Format: postgresql+psycopg2://user:password@host:port/database
  value = "postgresql+psycopg2://postgres:${var.database_password}@db.${supabase_project.main.id}.supabase.co:5432/postgres"
  sensitive = true
}

