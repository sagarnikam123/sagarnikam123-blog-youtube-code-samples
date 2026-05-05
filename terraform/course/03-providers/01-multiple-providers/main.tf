# =============================================================================
# Module 03 — Exercise 1: Multiple Providers
# =============================================================================
# Use Docker, Random, and Local providers together in one config.
# Shows how Terraform can orchestrate across multiple provider types.
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

provider "docker" {}
provider "random" {}
provider "local" {}

# Generate a random suffix for unique naming
resource "random_pet" "suffix" {
  length = 2
}

# Pull an image
resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  keep_locally = true
}

# Run a container with a random name
resource "docker_container" "web" {
  name  = "web-${random_pet.suffix.id}"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = 8081
  }
}

# Write container info to a local file
resource "local_file" "container_info" {
  filename = "${path.module}/output/container-info.txt"
  content  = <<-EOT
    Container Name: ${docker_container.web.name}
    Container ID:   ${docker_container.web.id}
    Image:          ${docker_image.nginx.name}
    Access URL:     http://localhost:8081
    Random Suffix:  ${random_pet.suffix.id}
  EOT
}

output "container_name" {
  value = docker_container.web.name
}

output "url" {
  value = "http://localhost:8081"
}
