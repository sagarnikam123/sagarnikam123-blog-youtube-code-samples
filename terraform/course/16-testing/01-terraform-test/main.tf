# =============================================================================
# Module 16 — Exercise 1: Terraform Test
# =============================================================================
# Terraform has a built-in test framework (terraform test).
# Test files use .tftest.hcl extension and live in a tests/ directory.
#
# Run:
#   terraform init
#   terraform test              # run all tests
#   terraform test -verbose     # verbose output
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

provider "local" {}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "myapp"
}

variable "port" {
  description = "Application port"
  type        = number
  default     = 8080

  validation {
    condition     = var.port >= 1024 && var.port <= 65535
    error_message = "Port must be between 1024 and 65535."
  }
}

locals {
  config_content = <<-EOT
    environment: ${var.environment}
    app_name:    ${var.app_name}
    port:        ${var.port}
  EOT
}

resource "local_file" "config" {
  filename = "${path.module}/output/${var.environment}-config.txt"
  content  = local.config_content
}

output "environment" {
  value = var.environment
}

output "port" {
  value = var.port
}

output "config_file" {
  value = local_file.config.filename
}
