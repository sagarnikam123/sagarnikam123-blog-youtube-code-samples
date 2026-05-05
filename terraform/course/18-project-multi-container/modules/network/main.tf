# =============================================================================
# Module: network — Creates a Docker network
# =============================================================================

terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

variable "network_name" {
  description = "Name of the Docker network"
  type        = string
}

variable "subnet" {
  description = "CIDR subnet for the network"
  type        = string
  default     = "172.30.0.0/16"
}

resource "docker_network" "this" {
  name = var.network_name

  ipam_config {
    subnet = var.subnet
  }
}

output "network_id" {
  description = "ID of the created network"
  value       = docker_network.this.id
}

output "network_name" {
  description = "Name of the created network"
  value       = docker_network.this.name
}
