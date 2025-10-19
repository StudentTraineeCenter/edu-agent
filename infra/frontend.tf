
resource "azurerm_linux_web_app" "web" {
  name                = "${local.name_prefix}-web"
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
    health_check_path                       = "/"
    health_check_eviction_time_in_min       = 10
    ftps_state                              = "Disabled"
    minimum_tls_version                     = "1.2"
    http2_enabled                           = true
  }

  identity {
    type = "SystemAssigned"
  }

  # Minimal settings for NGINX-based SPA container
  app_settings = {
    "WEBSITES_PORT"                       = "80"    # NGINX default
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = "false" # use container image only

    # Frontend environment variables
    "VITE_AZURE_ENTRA_TENANT_ID" = var.azure_tenant_id
    "VITE_AZURE_ENTRA_CLIENT_ID" = var.azure_app_client_id

    # URLs — dynamically built from the App Service FQDN
    "VITE_SERVER_URL" = "https://${azurerm_linux_web_app.api.default_hostname}"
  }

  tags = local.common_tags
}
