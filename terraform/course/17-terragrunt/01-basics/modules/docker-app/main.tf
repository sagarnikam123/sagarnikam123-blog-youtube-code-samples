# =============================================================================
# Reusable Terraform module for Terragrunt exercises
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

variable "app_name" {
  type = string
}

variable "image" {
  type    = string
  default = "nginx:alpine"
}

variable "external_port" {
  type = number
}

variable "environment" {
  type    = string
  default = "dev"
}

resource "docker_image" "app" {
  name         = var.image
  keep_locally = true
}

resource "docker_container" "app" {
  name  = "${var.app_name}-${var.environment}"
  image = docker_image.app.image_id

  ports {
    internal = 80
    external = var.external_port
  }

  env = [
    "APP_NAME=${var.app_name}",
    "ENVIRONMENT=${var.environment}",
  ]
}

output "container_name" {
  value = docker_container.app.name
}

output "container_id" {
  value = docker_container.app.id
}

output "access_url" {
  value = "http://localhost:${var.external_port}"
}
