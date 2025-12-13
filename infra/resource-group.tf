# ============================================================================
# Random Suffix for Unique Resource Naming
# ============================================================================
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# ============================================================================
# Resource Group
# ============================================================================
resource "azurerm_resource_group" "main" {
  name     = local.resource_group_name
  location = var.location

  tags = local.common_tags
}

# ============================================================================
# Grant Current User Full Access to Resource Group
# This ensures the user running Terraform has permissions to manage all resources
# ============================================================================
data "azurerm_client_config" "current" {}

resource "azurerm_role_assignment" "current_user_resource_group_contributor" {
  scope                = azurerm_resource_group.main.id
  role_definition_name = "Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
  
  depends_on = [azurerm_resource_group.main]
}

