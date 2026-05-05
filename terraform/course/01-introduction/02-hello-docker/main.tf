# =============================================================================
# Module 01 — Exercise 2: Hello Docker
# =============================================================================
# Run an Nginx container using Terraform + Docker provider.
# After apply, visit http://localhost:8080 to see the Nginx welcome page.
#
# Prerequisites: Docker Desktop must be running.
#
# Usage:
#   terraform init
#   terraform plan
#   terraform apply
#   curl http://localhost:8080    # or open in browser
#   terraform destroy             # stop and remove the container
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

# Connect to the local Docker daemon
provider "docker" {}

# Pull the Nginx image
resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  keep_locally = true # Don't delete the image on terraform destroy
}

# Run a container from the image
resource "docker_container" "nginx" {
  name  = "hello-terraform-nginx"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = 8080
  }
}

# Output the container name and access URL
output "container_name" {
  description = "Name of the running container"
  value       = docker_container.nginx.name
}

output "access_url" {
  description = "URL to access the Nginx server"
  value       = "http://localhost:8080"
}
