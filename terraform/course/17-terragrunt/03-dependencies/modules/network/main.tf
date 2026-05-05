terraform {
  required_version = ">= 1.15.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

variable "network_name" {
  type = string
}

resource "docker_network" "this" {
  name = var.network_name
}

output "network_id" {
  value = docker_network.this.id
}

output "network_name" {
  value = docker_network.this.name
}
