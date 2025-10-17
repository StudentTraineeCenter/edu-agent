terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "4.49.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "3.7.2"
    }
  }

  # Uncomment and configure for remote state storage
  # backend "azurerm" {
  #   storage_account_name = "your_storage_account_name"
  #   container_name       = "tfstate"
  #   key                  = "terraform.tfstate"
  #   resource_group_name  = "rg-terraform-state"
  # }
}

provider "azurerm" {
  subscription_id = var.azure_subscription_id
  tenant_id = var.azure_tenant_id
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}
