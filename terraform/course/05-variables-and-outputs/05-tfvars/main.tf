# =============================================================================
# Module 05 — Exercise 5: Tfvars Files
# =============================================================================
# Use .tfvars files to set variable values for different environments.
#
# Try:
#   terraform plan                                          # uses defaults
#   terraform plan -var-file="environments/dev.tfvars"      # dev settings
#   terraform plan -var-file="environments/staging.tfvars"  # staging settings
#   terraform plan -var-file="environments/prod.tfvars"     # prod settings
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
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "myapp"
}

variable "replica_count" {
  description = "Number of replicas"
  type        = number
  default     = 1
}

variable "enable_debug" {
  description = "Enable debug mode"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default = {
    managed_by = "terraform"
  }
}

resource "local_file" "env_config" {
  filename = "${path.module}/output/${var.environment}-config.txt"
  content  = <<-EOT
    === ${upper(var.environment)} Environment ===
    App Name:      ${var.app_name}
    Replicas:      ${var.replica_count}
    Debug Mode:    ${var.enable_debug}
    Tags:          ${jsonencode(var.tags)}
  EOT
}

output "environment" {
  value = var.environment
}

output "config_file" {
  value = local_file.env_config.filename
}
