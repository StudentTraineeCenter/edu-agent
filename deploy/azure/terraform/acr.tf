# ============================================================================
# Azure Container Registry
# ============================================================================
# Used for hosting container images for API, worker, and web applications.
# Provides private container registry with managed identity authentication.

resource "azurerm_container_registry" "acr" {
  name                = local.acr_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Standard"
  admin_enabled       = false

  tags = local.common_tags
}

