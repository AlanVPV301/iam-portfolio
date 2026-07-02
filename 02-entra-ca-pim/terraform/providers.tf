terraform {
  required_providers {
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 3.0"
    }
  }
}

provider "azuread" {
  tenant_id = var.tenant_id
  # Uses ARM_CLIENT_ID / ARM_CLIENT_SECRET / ARM_TENANT_ID from env
}