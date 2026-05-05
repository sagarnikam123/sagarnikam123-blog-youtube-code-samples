# =============================================================================
# Module: docker-app
# =============================================================================
# A reusable module that creates a Docker container with an image,
# network, and port mapping.
# =============================================================================

terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

resource "docker_image" "app" {
  name         = var.image
  keep_locally = true
}

resource "docker_container" "app" {
  name  = var.app_name
  image = docker_image.app.image_id

  ports {
    internal = var.internal_port
    external = var.external_port
  }

  env = [for k, v in var.env_vars : "${k}=${v}"]
}
