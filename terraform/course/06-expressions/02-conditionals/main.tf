# =============================================================================
# Module 06 — Exercise 2: Conditional Expressions
# =============================================================================
# The ternary operator: condition ? true_value : false_value
#
# Try:
#   terraform plan -var 'environment=prod'
#   terraform plan -var 'environment=dev'
#   terraform plan -var 'enable_monitoring=false'
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
}

variable "enable_monitoring" {
  type    = bool
  default = true
}

locals {
  # Conditional values based on environment
  container_name = var.environment == "prod" ? "app-production" : "app-${var.environment}"
  port           = var.environment == "prod" ? 80 : 8085
  log_level      = var.environment == "prod" ? "warn" : "debug"
  replicas       = var.environment == "prod" ? 3 : 1

  # Conditional with bool
  monitoring_label = var.enable_monitoring ? "enabled" : "disabled"
}

resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  keep_locally = true
}

resource "docker_container" "app" {
  name  = local.container_name
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = local.port
  }

  env = [
    "ENVIRONMENT=${var.environment}",
    "LOG_LEVEL=${local.log_level}",
    "MONITORING=${local.monitoring_label}",
  ]
}

resource "local_file" "config" {
  filename = "${path.module}/output/conditional-config.txt"
  content  = <<-EOT
    Environment:  ${var.environment}
    Container:    ${local.container_name}
    Port:         ${local.port}
    Log Level:    ${local.log_level}
    Replicas:     ${local.replicas}
    Monitoring:   ${local.monitoring_label}
  EOT
}

output "container_name" {
  value = local.container_name
}

output "access_url" {
  value = "http://localhost:${local.port}"
}
