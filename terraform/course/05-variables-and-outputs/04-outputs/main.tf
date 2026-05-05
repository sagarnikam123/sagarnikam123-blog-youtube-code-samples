# =============================================================================
# Module 05 — Exercise 4: Outputs
# =============================================================================
# Outputs expose values after apply. They're essential for:
# - Displaying useful info (URLs, IDs, names)
# - Passing data between modules
# - Querying with `terraform output`
#
# Try:
#   terraform apply
#   terraform output                    # show all outputs
#   terraform output container_id       # show one output
#   terraform output -json              # JSON format
#   terraform output -raw access_url    # raw value (no quotes)
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

resource "random_pet" "name" {
  length = 2
}

resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  keep_locally = true
}

resource "docker_container" "web" {
  name  = "output-demo-${random_pet.name.id}"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = 8084
  }
}

# --- Simple string output ---
output "container_name" {
  description = "Name of the running container"
  value       = docker_container.web.name
}

# --- Computed attribute output ---
output "container_id" {
  description = "Docker container ID"
  value       = docker_container.web.id
}

# --- Formatted output ---
output "access_url" {
  description = "URL to access the web server"
  value       = "http://localhost:8084"
}

# --- Complex output (map) ---
output "container_details" {
  description = "Full container details as a map"
  value = {
    name  = docker_container.web.name
    id    = docker_container.web.id
    image = docker_image.nginx.name
    port  = 8084
  }
}

# --- List output ---
output "all_resource_names" {
  description = "Names of all resources created"
  value = [
    random_pet.name.id,
    docker_image.nginx.name,
    docker_container.web.name,
  ]
}
