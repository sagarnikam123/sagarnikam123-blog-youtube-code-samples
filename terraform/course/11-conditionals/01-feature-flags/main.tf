# =============================================================================
# Module 11 — Exercise 1: Feature Flags
# =============================================================================
# Use boolean variables as feature flags to toggle resources.
#
# Try:
#   terraform plan -var 'enable_cache=false'
#   terraform plan -var 'enable_logging=false' -var 'enable_cache=false'
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

variable "enable_web" {
  description = "Deploy the web server"
  type        = bool
  default     = true
}

variable "enable_cache" {
  description = "Deploy a cache container"
  type        = bool
  default     = true
}

variable "enable_logging" {
  description = "Enable logging configuration"
  type        = bool
  default     = true
}

resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  keep_locally = true
}

# Conditional resource: web server
resource "docker_container" "web" {
  count = var.enable_web ? 1 : 0

  name  = "feature-flag-web"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = 9040
  }
}

# Conditional resource: cache
resource "docker_container" "cache" {
  count = var.enable_cache ? 1 : 0

  name  = "feature-flag-cache"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = 9041
  }
}

# Conditional file creation
resource "local_file" "logging_config" {
  count = var.enable_logging ? 1 : 0

  filename = "${path.module}/output/logging.txt"
  content  = "Logging is enabled"
}

# Summary
resource "local_file" "summary" {
  filename = "${path.module}/output/feature-flags.txt"
  content  = <<-EOT
    === Feature Flags ===
    Web Server:  ${var.enable_web ? "ENABLED" : "DISABLED"}
    Cache:       ${var.enable_cache ? "ENABLED" : "DISABLED"}
    Logging:     ${var.enable_logging ? "ENABLED" : "DISABLED"}

    Active containers: ${(var.enable_web ? 1 : 0) + (var.enable_cache ? 1 : 0)}
  EOT
}

output "web_url" {
  value = var.enable_web ? "http://localhost:9040" : "disabled"
}

output "cache_url" {
  value = var.enable_cache ? "http://localhost:9041" : "disabled"
}
