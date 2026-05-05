terraform {
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
  description = "Docker network ID to attach to"
  type        = string
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
    internal = 80
    external = var.external_port
  }
}

output "container_name" {
  value = docker_container.this.name
}

output "access_url" {
  value = "http://localhost:${var.external_port}"
}
