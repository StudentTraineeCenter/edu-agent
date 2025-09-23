# Azure AI Search Service
resource "azurerm_search_service" "main" {
  name                = "${replace(var.project_name, "-", "")}${var.environment}${random_string.suffix.result}search"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "basic"  # Use standard for production, basic for dev

  tags = local.common_tags
}
