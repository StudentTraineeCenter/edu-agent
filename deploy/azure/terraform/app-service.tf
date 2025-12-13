# ============================================================================
# App Service Plan & Web App
# ============================================================================
resource "azurerm_service_plan" "web" {
  name                = local.app_service_plan_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = var.app_service_os_type
  sku_name            = var.app_service_sku_name

  tags = local.common_tags
}

resource "azurerm_linux_web_app" "web" {
  name                = local.web_app_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  service_plan_id     = azurerm_service_plan.web.id
  https_only          = true

  site_config {
    application_stack {
      docker_image_name   = "${var.acr_repository_web}:${var.acr_tag_web}"
      docker_registry_url = "https://${azurerm_container_registry.acr.login_server}"
    }

    container_registry_use_managed_identity = true
    always_on                               = true
    health_check_path                       = var.web_health_check_path
    health_check_eviction_time_in_min       = var.health_check_eviction_time_in_min
    ftps_state                              = "Disabled"
    minimum_tls_version                     = "1.2"
    http2_enabled                           = true
    # Enable continuous deployment - App Service will check for new images periodically
    # Webhooks provide immediate trigger, this is a fallback
  }

  identity {
    type = "SystemAssigned"
  }

  app_settings = {
    "WEBSITES_PORT"                       = "80"
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = "false"

    # Frontend environment variables - Supabase
    "VITE_SUPABASE_URL"     = "https://${supabase_project.main.id}.supabase.co"
    "VITE_SUPABASE_ANON_KEY" = var.supabase_anon_key != null ? var.supabase_anon_key : ""

    # URLs - constructed from container app FQDN
    "VITE_SERVER_URL" = "https://${azurerm_container_app.api.latest_revision_fqdn}"
  }

  depends_on = [azurerm_container_app.api]

  tags = local.common_tags
}

