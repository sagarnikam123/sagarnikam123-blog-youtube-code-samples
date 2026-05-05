# =============================================================================
# Module 10 — Exercise 1: Count
# =============================================================================
# Create multiple resources using count.
#
# Try:
#   terraform plan -var 'container_count=5'
#   terraform plan -var 'container_count=0'   # creates nothing
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

provider "docker" {}
provider "local" {}

variable "container_count" {
  description = "Number of containers to create"
  type        = number
  default     = 3

  validation {
    condition     = var.container_count >= 0 && var.container_count <= 10
    error_message = "Container count must be between 0 and 10."
  }
}

resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  keep_locally = true
}

# Create N containers using count
resource "docker_container" "web" {
  count = var.container_count

  name  = "count-demo-${count.index}"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = 9010 + count.index # 9010, 9011, 9012, ...
  }

  env = [
    "INSTANCE_INDEX=${count.index}",
    "INSTANCE_TOTAL=${var.container_count}",
  ]
}

# Conditional resource using count as a toggle
variable "enable_monitoring" {
  type    = bool
  default = true
}

resource "local_file" "monitoring_config" {
  count = var.enable_monitoring ? 1 : 0

  filename = "${path.module}/output/monitoring.txt"
  content  = "Monitoring is enabled for ${var.container_count} containers."
}

# Outputs
output "container_names" {
  description = "Names of all created containers"
  value       = docker_container.web[*].name
}

output "container_urls" {
  description = "URLs for all containers"
  value       = [for i in range(var.container_count) : "http://localhost:${9010 + i}"]
}

output "monitoring_enabled" {
  value = var.enable_monitoring
}
