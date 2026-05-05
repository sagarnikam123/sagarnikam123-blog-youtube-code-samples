# =============================================================================
# Module 09 — Exercise 3: Module with for_each
# =============================================================================
# Create multiple instances of a module using for_each.
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

variable "apps" {
  description = "Map of applications to deploy"
  type = map(object({
    image         = string
    external_port = number
  }))
  default = {
    web = {
      image         = "nginx:alpine"
      external_port = 9001
    }
    api = {
      image         = "httpd:alpine"
      external_port = 9002
    }
    docs = {
      image         = "nginx:alpine"
      external_port = 9003
    }
  }
}

# Reuse the docker-app module from exercise 1
module "apps" {
  source   = "../01-local-module/modules/docker-app"
  for_each = var.apps

  app_name      = "foreach-${each.key}"
  image         = each.value.image
  external_port = each.value.external_port
}

output "app_urls" {
  description = "URLs for all deployed apps"
  value       = { for name, app in module.apps : name => app.access_url }
}

output "app_containers" {
  description = "Container names for all apps"
  value       = { for name, app in module.apps : name => app.container_name }
}
