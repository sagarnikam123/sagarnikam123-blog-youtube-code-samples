# =============================================================================
# Module 10 — Exercise 2: For Each
# =============================================================================
# Create resources from maps and sets — more stable than count.
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

# --- for_each with a set ---
variable "environments" {
  type    = set(string)
  default = ["dev", "staging", "prod"]
}

resource "local_file" "env_configs" {
  for_each = var.environments

  filename = "${path.module}/output/${each.key}-config.txt"
  content  = "Configuration for ${each.key} environment"
}

# --- for_each with a map ---
variable "containers" {
  description = "Map of containers to create"
  type = map(object({
    image         = string
    external_port = number
  }))
  default = {
    frontend = {
      image         = "nginx:alpine"
      external_port = 9020
    }
    backend = {
      image         = "httpd:alpine"
      external_port = 9021
    }
    cache = {
      image         = "nginx:alpine"
      external_port = 9022
    }
  }
}

resource "docker_image" "apps" {
  for_each = toset(distinct([for c in var.containers : c.image]))

  name         = each.key
  keep_locally = true
}

resource "docker_container" "apps" {
  for_each = var.containers

  name  = "foreach-${each.key}"
  image = docker_image.apps[each.value.image].image_id

  ports {
    internal = 80
    external = each.value.external_port
  }

  env = [
    "SERVICE_NAME=${each.key}",
  ]
}

output "container_details" {
  description = "Details of all containers"
  value = {
    for name, container in docker_container.apps : name => {
      name = container.name
      url  = "http://localhost:${var.containers[name].external_port}"
    }
  }
}

output "env_config_files" {
  value = [for f in local_file.env_configs : f.filename]
}
