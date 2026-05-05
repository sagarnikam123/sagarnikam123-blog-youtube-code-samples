# =============================================================================
# Module 17 — Exercise 1: Terragrunt Basics
# =============================================================================
# This is the simplest Terragrunt config.
# It inherits provider/version config from root.hcl and calls a module.
#
# Usage:
#   cd live/web-app
#   terragrunt init
#   terragrunt plan
#   terragrunt apply
#   terragrunt destroy
# =============================================================================

# Include the root config (provider, versions)
include "root" {
  path = find_in_parent_folders("root.hcl")
}

# Point to the Terraform module
terraform {
  source = "../../modules/docker-app"
}

# Pass inputs to the module
inputs = {
  app_name      = "tg-basics"
  image         = "nginx:alpine"
  external_port = 9200
  environment   = "dev"
}
