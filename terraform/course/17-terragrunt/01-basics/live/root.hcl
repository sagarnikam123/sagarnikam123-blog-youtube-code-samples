# =============================================================================
# Root Terragrunt config — shared by all child modules
# =============================================================================
# This file is found by child configs using find_in_parent_folders("root.hcl")
# =============================================================================

# Generate provider configuration in every child module
generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<-EOF
    provider "docker" {}
  EOF
}

# Generate terraform version constraint
generate "versions" {
  path      = "versions.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<-EOF
    terraform {
      required_version = ">= 1.15.0"

      required_providers {
        docker = {
          source  = "kreuzwerker/docker"
          version = "~> 3.0"
        }
      }
    }
  EOF
}
