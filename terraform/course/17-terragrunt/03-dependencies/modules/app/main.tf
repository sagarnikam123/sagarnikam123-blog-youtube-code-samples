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

variable "network_id" {
  type = string
}

resource "docker_image" "app" {
  name         = var.image
  keep_locally = true
}

resource "docker_container" "app" {
  name  = var.app_name
  image = docker_image.app.image_id

  networks_advanced {
    name = var.network_id
  }

  ports {
    internal = 80
    external = var.external_port
  }
}

output "container_name" {
  value = docker_container.app.name
}

output "access_url" {
  value = "http://localhost:${var.external_port}"
}
