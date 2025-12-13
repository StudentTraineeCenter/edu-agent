# ============================================================================
# Supabase Project
# ============================================================================
# Note: Site URL will be updated after app service is created via a separate
# terraform apply or manually in Supabase dashboard

resource "supabase_project" "main" {
  organization_id   = var.supabase_organization_id
  name              = "${local.org_short}-${local.env_short}"
  database_password = var.supabase_database_password
  region            = var.supabase_region

  lifecycle {
    ignore_changes = [database_password, name]
  }
}

# ============================================================================
# Supabase Settings
# ============================================================================
resource "supabase_settings" "main" {
  project_ref = supabase_project.main.id

  api = jsonencode({
    db_schema            = "public,storage,graphql_public"
    db_extra_search_path = "public,extensions"
    max_rows             = 1000
  })

  auth = jsonencode({
    site_url = "http://localhost:3000"  # Will be updated after deployment
  })
}

