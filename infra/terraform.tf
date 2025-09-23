terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~>3.1"
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
  features {}
}
