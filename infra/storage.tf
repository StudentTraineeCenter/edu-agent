# Storage Account is now defined in rbac.tf with managed identity

# Blob Containers
resource "azurerm_storage_container" "documents" {
  name                  = "documents"
  storage_account_id = azurerm_storage_account.main.id
  container_access_type = "private"
}
