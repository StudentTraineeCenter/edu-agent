# Storage Account for Blob Storage
resource "azurerm_storage_account" "main" {
  name                     = "${replace(var.project_name, "-", "")}${var.environment}${random_string.suffix.result}sa"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = local.common_tags
}

# Blob Containers
resource "azurerm_storage_container" "documents" {
  name                  = "documents"
  storage_account_name = azurerm_storage_account.main.name
  container_access_type = "private"
}
