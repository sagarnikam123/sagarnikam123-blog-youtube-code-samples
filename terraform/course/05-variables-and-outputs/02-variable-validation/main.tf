# =============================================================================
# Module 05 — Exercise 2: Variable Validation
# =============================================================================
# Custom validation rules ensure variables meet your requirements
# BEFORE Terraform tries to create resources.
#
# Try:
#   terraform plan                                    # uses defaults (passes)
#   terraform plan -var 'environment=invalid'         # fails validation
#   terraform plan -var 'port=99999'                  # fails validation
#   terraform plan -var 'email=not-an-email'          # fails validation
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

# --- Validation: allowed values (enum-like) ---
variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

# --- Validation: numeric range ---
variable "port" {
  description = "Application port"
  type        = number
  default     = 8080

  validation {
    condition     = var.port >= 1024 && var.port <= 65535
    error_message = "Port must be between 1024 and 65535."
  }
}

# --- Validation: string pattern (regex) ---
variable "app_name" {
  description = "Application name (lowercase alphanumeric and hyphens only)"
  type        = string
  default     = "my-app"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,62}[a-z0-9]$", var.app_name))
    error_message = "App name must be 3-64 chars, lowercase alphanumeric and hyphens, start with letter, end with alphanumeric."
  }
}

# --- Validation: string format ---
variable "email" {
  description = "Contact email"
  type        = string
  default     = "admin@example.com"

  validation {
    condition     = can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.email))
    error_message = "Must be a valid email address."
  }
}

# --- Validation: list length ---
variable "tags_list" {
  description = "List of tags (1-5 tags required)"
  type        = list(string)
  default     = ["terraform", "learning"]

  validation {
    condition     = length(var.tags_list) >= 1 && length(var.tags_list) <= 5
    error_message = "Must provide between 1 and 5 tags."
  }
}

resource "local_file" "validation_result" {
  filename = "${path.module}/output/validated-config.txt"
  content  = <<-EOT
    All validations passed!
    Environment: ${var.environment}
    Port:        ${var.port}
    App Name:    ${var.app_name}
    Email:       ${var.email}
    Tags:        ${join(", ", var.tags_list)}
  EOT
}

output "status" {
  value = "All validations passed — config written to output/"
}
