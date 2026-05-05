# =============================================================================
# Module: app — Creates a Docker container attached to a network
# =============================================================================

terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

resource "docker_image" "this" {
  name         = var.image
  keep_locally = true
}

resource "docker_container" "this" {
  name  = var.app_name
  image = docker_image.this.image_id

  networks_advanced {
    name = var.network_id
  }

  ports {
    internal = var.internal_port
    external = var.external_port
  }

  env = [for k, v in var.env_vars : "${k}=${v}"]

  dynamic "volumes" {
    for_each = var.volumes
    content {
      host_path      = volumes.value.host_path
      container_path = volumes.value.container_path
      read_only      = volumes.value.read_only
    }
  }
}
