# =============================================================================
# BROKEN CONFIG — Sensitive Output
# =============================================================================
# This config generates a password but exposes it in a non-sensitive output.
#
# Your task:
#   1. Run `terraform plan` — see the error about sensitive values
#   2. Fix the output so Terraform allows it
#   3. Understand when to use `sensitive = true` vs `nonsensitive()`
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "random" {}

resource "random_password" "db" {
  length  = 24
  special = true
}

# BUG: This output references a sensitive value without marking it sensitive
output "database_password" {
  description = "The generated database password"
  value       = random_password.db.result
}

# BUG: This also leaks the sensitive value inside a string
output "connection_string" {
  description = "Database connection string"
  value       = "postgres://admin:${random_password.db.result}@localhost:5432/mydb"
}
