# =============================================================================
# Module 10 — Exercise 3: Dynamic Blocks
# =============================================================================
# Generate repeated nested blocks dynamically.
# Useful when the number of nested blocks varies based on input.
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

variable "port_mappings" {
  description = "List of port mappings for the container"
  type = list(object({
    internal = number
    external = number
    protocol = optional(string, "tcp")
  }))
  default = [
    { internal = 80, external = 9030 },
    { internal = 443, external = 9031 },
    { internal = 8080, external = 9032 },
  ]
}

variable "volumes" {
  description = "List of volume mounts"
  type = list(object({
    host_path      = string
    container_path = string
    read_only      = optional(bool, false)
  }))
  default = []
}

variable "env_vars" {
  description = "Environment variables"
  type        = map(string)
  default = {
    APP_ENV   = "development"
    LOG_LEVEL = "debug"
    TZ        = "UTC"
  }
}

resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  keep_locally = true
}

resource "docker_container" "app" {
  name  = "dynamic-blocks-demo"
  image = docker_image.nginx.image_id

  # Dynamic ports block
  dynamic "ports" {
    for_each = var.port_mappings
    content {
      internal = ports.value.internal
      external = ports.value.external
      protocol = ports.value.protocol
    }
  }

  # Dynamic volumes block (only if volumes are provided)
  dynamic "volumes" {
    for_each = var.volumes
    content {
      host_path      = volumes.value.host_path
      container_path = volumes.value.container_path
      read_only      = volumes.value.read_only
    }
  }

  # Environment variables from map
  env = [for k, v in var.env_vars : "${k}=${v}"]
}

resource "local_file" "dynamic_summary" {
  filename = "${path.module}/output/dynamic-blocks-summary.txt"
  content  = <<-EOT
    === Dynamic Blocks Demo ===

    Container: ${docker_container.app.name}

    Port Mappings:
    %{for pm in var.port_mappings~}
      ${pm.internal} -> ${pm.external} (${pm.protocol})
    %{endfor~}

    Environment Variables:
    %{for k, v in var.env_vars~}
      ${k}=${v}
    %{endfor~}

    Volume Mounts: ${length(var.volumes) > 0 ? length(var.volumes) : "none"}
  EOT
}

output "container_name" {
  value = docker_container.app.name
}

output "port_urls" {
  value = [for pm in var.port_mappings : "http://localhost:${pm.external}"]
}
