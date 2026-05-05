# =============================================================================
# Module 02 — Exercise 2: Multiple Files — providers.tf
# =============================================================================
# Demonstrates splitting configuration across multiple .tf files.
# Terraform loads ALL .tf files in a directory — order doesn't matter.
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "local" {}
provider "random" {}
