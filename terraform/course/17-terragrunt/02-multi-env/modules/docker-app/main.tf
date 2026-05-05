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
  type = string
}

variable "replicas" {
  type    = number
  default = 1
}

resource "docker_image" "app" {
  name         = var.image
  keep_locally = true
}

resource "docker_container" "app" {
  count = var.replicas

  name  = "${var.app_name}-${var.environment}-${count.index}"
  image = docker_image.app.image_id

  ports {
    internal = 80
    external = var.external_port + count.index
  }

  env = [
    "APP_NAME=${var.app_name}",
    "ENVIRONMENT=${var.environment}",
    "INSTANCE=${count.index}",
  ]
}

output "container_names" {
  value = docker_container.app[*].name
}

output "access_urls" {
  value = [for i in range(var.replicas) : "http://localhost:${var.external_port + i}"]
}
