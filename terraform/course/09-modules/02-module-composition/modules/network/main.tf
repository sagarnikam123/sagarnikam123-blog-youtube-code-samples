terraform {
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

variable "subnet" {
  type    = string
  default = "172.28.0.0/16"
}

resource "docker_network" "this" {
  name = var.network_name

  ipam_config {
    subnet = var.subnet
  }
}

output "network_id" {
  value = docker_network.this.id
}

output "network_name" {
  value = docker_network.this.name
}
