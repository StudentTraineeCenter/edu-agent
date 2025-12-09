resource "azurerm_service_plan" "web" {
  name                = var.service_plan_name
  location            = var.location
  resource_group_name = var.resource_group_name
  os_type             = var.os_type
  sku_name            = var.sku_name

  tags = var.tags
}

resource "azurerm_linux_web_app" "server" {
  name                = var.server_app_name
  location            = var.location
  resource_group_name = var.resource_group_name
  service_plan_id     = azurerm_service_plan.web.id
  https_only          = true

  site_config {
    application_stack {
      docker_image_name   = "${var.acr_repository_server}:${var.acr_tag_server}"
      docker_registry_url = "https://${var.acr_login_server}"
    }

    container_registry_use_managed_identity = true
    always_on                               = true
    health_check_path                       = var.server_health_check_path
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

  app_settings = var.server_app_settings

  tags = var.tags
}

resource "azurerm_linux_web_app" "web" {
  name                = var.web_app_name
  location            = var.location
  resource_group_name = var.resource_group_name
  service_plan_id     = azurerm_service_plan.web.id
  https_only          = true

  site_config {
    application_stack {
      docker_image_name   = "${var.acr_repository_web}:${var.acr_tag_web}"
      docker_registry_url = "https://${var.acr_login_server}"
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

  app_settings = var.web_app_settings

  tags = var.tags
}

