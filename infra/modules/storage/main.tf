resource "azurerm_storage_account" "main" {
  name                     = var.storage_account_name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = var.account_tier
  account_replication_type = var.account_replication_type
  account_kind             = var.account_kind

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

resource "azurerm_storage_container" "input" {
  name                  = "input"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = var.container_access_type
}

resource "azurerm_storage_container" "output" {
  name                  = "output"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = var.container_access_type
}

