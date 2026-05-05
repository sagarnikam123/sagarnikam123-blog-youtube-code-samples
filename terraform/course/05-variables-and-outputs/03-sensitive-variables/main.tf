# =============================================================================
# Module 05 — Exercise 3: Sensitive Variables
# =============================================================================
# Sensitive variables are hidden from CLI output and plan display.
# Terraform still stores them in state — state files must be protected!
#
# Try:
#   terraform plan                          # notice "(sensitive value)" in output
#   terraform output                        # sensitive outputs are hidden
#   terraform output -json                  # JSON shows all values (be careful!)
#   terraform output db_password            # shows: sensitive
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

provider "random" {}
provider "local" {}

# --- Sensitive input variable ---
variable "db_password" {
  description = "Database password"
  type        = string
  default     = "super-secret-password-123"
  sensitive   = true
}

variable "api_key" {
  description = "API key for external service"
  type        = string
  default     = "ak_live_abc123def456"
  sensitive   = true
}

# --- Generate a random password ---
resource "random_password" "generated" {
  length           = 24
  special          = true
  override_special = "!@#$%"
}

# --- Write a non-sensitive summary ---
resource "local_file" "config" {
  filename = "${path.module}/output/config-summary.txt"
  content  = <<-EOT
    Database: configured (password hidden)
    API Key:  configured (key hidden)
    Generated password length: ${length(random_password.generated.result)} chars
  EOT
}

# --- Outputs ---
output "db_password" {
  description = "The database password (marked sensitive)"
  value       = var.db_password
  sensitive   = true
}

output "generated_password" {
  description = "A randomly generated password"
  value       = random_password.generated.result
  sensitive   = true
}

output "non_sensitive_info" {
  description = "Safe to display"
  value       = "Config written. Use 'terraform output -json' to see sensitive values."
}
