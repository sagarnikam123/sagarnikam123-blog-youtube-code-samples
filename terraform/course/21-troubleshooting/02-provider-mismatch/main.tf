# =============================================================================
# BROKEN CONFIG — Provider Mismatch
# =============================================================================
# This config uses resources but has provider configuration issues.
#
# Your task:
#   1. Run `terraform init` — see what happens
#   2. Run `terraform validate` — read the error
#   3. Fix the provider configuration
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    # BUG 1: Wrong source — "hashicorp/docker" doesn't exist
    docker = {
      source  = "hashicorp/docker"
      version = "~> 3.0"
    }
    # BUG 2: Missing random provider declaration
  }
}

provider "docker" {}

resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  keep_locally = true
}

resource "docker_container" "web" {
  name  = "provider-debug"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = 9500
  }
}

# BUG 3: Uses random_pet but random provider is not declared
resource "random_pet" "name" {
  length = 2
}

output "pet_name" {
  value = random_pet.name.id
}
