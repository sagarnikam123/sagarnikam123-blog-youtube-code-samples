# =============================================================================
# Module 14 — Exercise 1: Workspace Basics
# =============================================================================
# Workspaces let you manage multiple environments with the same config.
# Each workspace has its own state file.
#
# Try:
#   terraform workspace list                    # see workspaces
#   terraform workspace new dev                 # create "dev" workspace
#   terraform workspace new staging             # create "staging" workspace
#   terraform workspace select dev              # switch to dev
#   terraform apply                             # apply in dev context
#   terraform workspace select staging          # switch to staging
#   terraform apply                             # apply in staging context
#   terraform workspace select default          # back to default
#   terraform workspace delete dev              # delete workspace (must destroy first)
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

provider "docker" {}
provider "local" {}

# terraform.workspace is a built-in variable
locals {
  workspace = terraform.workspace

  config = {
    default = { port = 9080, replicas = 1, log_level = "debug" }
    dev     = { port = 9081, replicas = 1, log_level = "debug" }
    staging = { port = 9082, replicas = 2, log_level = "info" }
    prod    = { port = 9083, replicas = 3, log_level = "warn" }
  }

  # Use workspace config if it exists, otherwise fall back to default
  current_config = lookup(local.config, local.workspace, local.config["default"])
}

resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  keep_locally = true
}

resource "docker_container" "app" {
  count = local.current_config.replicas

  name  = "ws-${local.workspace}-${count.index}"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = local.current_config.port + count.index
  }

  env = [
    "WORKSPACE=${local.workspace}",
    "LOG_LEVEL=${local.current_config.log_level}",
    "INSTANCE=${count.index}",
  ]
}

resource "local_file" "workspace_info" {
  filename = "${path.module}/output/${local.workspace}-info.txt"
  content  = <<-EOT
    === Workspace: ${local.workspace} ===
    Replicas:  ${local.current_config.replicas}
    Base Port: ${local.current_config.port}
    Log Level: ${local.current_config.log_level}
  EOT
}

output "workspace" {
  value = local.workspace
}

output "urls" {
  value = [for i in range(local.current_config.replicas) : "http://localhost:${local.current_config.port + i}"]
}
