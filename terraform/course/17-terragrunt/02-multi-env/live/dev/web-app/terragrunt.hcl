# =============================================================================
# Dev environment — web-app
# =============================================================================

include "root" {
  path = find_in_parent_folders("root.hcl")
}

# Read environment-specific config
locals {
  env_config = read_terragrunt_config(find_in_parent_folders("env.hcl"))
  env        = local.env_config.locals.environment
  replicas   = local.env_config.locals.replicas
  base_port  = local.env_config.locals.base_port
}

terraform {
  source = "../../../modules/docker-app"
}

inputs = {
  app_name      = "tg-web"
  image         = "nginx:alpine"
  external_port = local.base_port
  environment   = local.env
  replicas      = local.replicas
}
