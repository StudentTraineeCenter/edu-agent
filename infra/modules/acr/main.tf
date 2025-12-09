# ============================================================================
# Azure Container Registry
# ============================================================================
# Used for hosting container images for server and web applications.
# Provides private container registry with managed identity authentication.

resource "azurerm_container_registry" "acr" {
  name                = var.acr_name
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = var.sku
  admin_enabled       = var.admin_enabled

  tags = var.tags
}


