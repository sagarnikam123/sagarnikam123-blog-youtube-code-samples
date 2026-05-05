# =============================================================================
# Module 11 — Exercise 2: Environment-Based Configuration
# =============================================================================
# Use locals with conditionals to build environment-specific configs.
#
# Try:
#   terraform plan -var 'environment=prod'
#   terraform plan -var 'environment=staging'
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

variable "environment" {
  type    = string
  default = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Must be dev, staging, or prod."
  }
}

# Environment-specific configuration using a map lookup
locals {
  env_config = {
    dev = {
      replicas  = 1
      log_level = "debug"
      port      = 9050
    }
    staging = {
      replicas  = 2
      log_level = "info"
      port      = 9051
    }
    prod = {
      replicas  = 3
      log_level = "warn"
      port      = 9052
    }
  }

  config = local.env_config[var.environment]
}

resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  keep_locally = true
}

resource "docker_container" "app" {
  count = local.config.replicas

  name  = "env-${var.environment}-${count.index}"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = local.config.port + count.index
  }

  env = [
    "ENVIRONMENT=${var.environment}",
    "LOG_LEVEL=${local.config.log_level}",
    "INSTANCE=${count.index}",
  ]
}

resource "local_file" "env_summary" {
  filename = "${path.module}/output/${var.environment}-summary.txt"
  content  = <<-EOT
    === ${upper(var.environment)} Environment ===
    Replicas:  ${local.config.replicas}
    Log Level: ${local.config.log_level}
    Base Port: ${local.config.port}
    URLs:      ${join(", ", [for i in range(local.config.replicas) : "http://localhost:${local.config.port + i}"])}
  EOT
}

output "environment" {
  value = var.environment
}

output "urls" {
  value = [for i in range(local.config.replicas) : "http://localhost:${local.config.port + i}"]
}
