# ============================================================================
# Storage Account
# ============================================================================
resource "azurerm_storage_account" "main" {
  name                     = local.storage_account_name
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"

  # Network rules: Allow all networks by default
  # Azure services (like Azure OpenAI) can bypass network rules
  # This allows Azure Storage Explorer to work and Azure OpenAI to download files
  network_rules {
    default_action             = "Allow"
    bypass                     = ["AzureServices"] # Allow Azure services to bypass
    ip_rules                   = []
    virtual_network_subnet_ids = []
  }

  identity {
    type = "SystemAssigned"
  }

  tags = local.common_tags
}

# ============================================================================
# Storage Container
# ============================================================================

resource "azurerm_storage_container" "input" {
  name                  = "input"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "output" {
  name                  = "output"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

# ============================================================================
# Storage Queue
# ============================================================================
resource "azurerm_storage_queue" "ai_generation_tasks" {
  name              = "ai-generation-tasks"
  storage_account_id = azurerm_storage_account.main.id
}

