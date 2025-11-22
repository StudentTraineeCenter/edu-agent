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
    time = {
      source  = "hashicorp/time"
      version = "0.11.1"
    }
  }

  # Remote state backend configuration
  # Configure via backend-config flags or set variables
  # For local development: leave backend block commented out
  # For CI/CD: use backend-config flags in terraform init
  backend "azurerm" {
    # These values are provided via -backend-config flags
    # storage_account_name = ""  # Set via TF_BACKEND_STORAGE_ACCOUNT env var
    # container_name       = ""   # Set via TF_BACKEND_CONTAINER env var
    # key                  = ""   # Set via TF_BACKEND_KEY env var
    # resource_group_name  = ""   # Set via TF_BACKEND_RESOURCE_GROUP env var
  }
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
