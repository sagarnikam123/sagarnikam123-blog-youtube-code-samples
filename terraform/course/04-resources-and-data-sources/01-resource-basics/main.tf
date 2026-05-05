# =============================================================================
# Module 04 — Exercise 1: Resource Basics
# =============================================================================
# Create Docker resources and see how they reference each other.
# Demonstrates: resource creation, attribute references, resource addressing.
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
  }
}

provider "docker" {}
provider "random" {}

# --- Resource 1: Generate a random name ---
resource "random_pet" "app_name" {
  length    = 2
  separator = "-"
}

# --- Resource 2: Pull a Docker image ---
resource "docker_image" "httpd" {
  name         = "httpd:alpine"
  keep_locally = true
}

# --- Resource 3: Create a Docker network ---
resource "docker_network" "app_net" {
  name = "${random_pet.app_name.id}-network"
}

# --- Resource 4: Run a container (references image, network, and pet name) ---
resource "docker_container" "web" {
  name  = random_pet.app_name.id
  image = docker_image.httpd.image_id

  networks_advanced {
    name = docker_network.app_net.id
  }

  ports {
    internal = 80
    external = 8082
  }

  # Environment variables inside the container
  env = [
    "APP_NAME=${random_pet.app_name.id}",
  ]
}

# --- Outputs: show computed attributes ---
output "container_name" {
  description = "Name of the container"
  value       = docker_container.web.name
}

output "container_ip" {
  description = "Container IP on the custom network"
  value       = docker_container.web.network_data[0].ip_address
}

output "network_name" {
  description = "Docker network name"
  value       = docker_network.app_net.name
}

output "access_url" {
  value = "http://localhost:8082"
}
