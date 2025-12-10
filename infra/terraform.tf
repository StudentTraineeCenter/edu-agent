terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azapi = {
      source  = "Azure/azapi"
      version = "~> 2.8.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.13"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
    supabase = {
      source  = "supabase/supabase"
      version = "~> 1.0"
    }
  }

  # Optional: Configure remote state backend for team collaboration
  # Uncomment and configure when ready for shared state
  # backend "azurerm" {
  #   resource_group_name  = "terraform-state-rg"
  #   storage_account_name = "tfstate12345"
  #   container_name       = "tfstate"
  #   key                  = "edu-agent.tfstate"
  # }
}

provider "azapi" {
  # Uses Azure CLI authentication by default
}

provider "azurerm" {
  subscription_id = var.azure_subscription_id
  tenant_id       = var.azure_tenant_id

  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

provider "supabase" {
  access_token = var.supabase_access_token
}
