# ============================================================================
# ACR Webhooks for Auto-Deployment
# ============================================================================
# Webhooks trigger App Service container sync when images are pushed to ACR.
# When a new image is pushed matching the scope (repository:tag), the webhook
# calls the App Service's deployment trigger endpoint, causing it to immediately
# pull and deploy the new image.
#
# This enables continuous deployment workflow:
# 1. Build and push image to ACR
# 2. ACR webhook fires
# 3. App Service automatically pulls and deploys new image
#
# Note: App Services also poll ACR periodically, but webhooks provide immediate updates.
# Container Apps use continuous deployment via ACR integration, so webhooks
# are only needed for the web app on App Service.

resource "azurerm_container_registry_webhook" "deployment_webhooks" {
  for_each = local.acr_webhook_configs

  name                = "webhook${each.key}"
  resource_group_name = azurerm_resource_group.main.name
  registry_name       = azurerm_container_registry.acr.name
  location            = azurerm_resource_group.main.location
  service_uri         = each.value.service_uri
  status              = "enabled"
  scope               = each.value.scope
  actions             = each.value.actions
  custom_headers = {
    "Content-Type" = "application/json"
  }

  tags = local.common_tags

  depends_on = [
    azurerm_container_registry.acr,
    azurerm_linux_web_app.web
  ]
}

