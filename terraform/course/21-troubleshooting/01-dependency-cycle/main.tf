# =============================================================================
# BROKEN CONFIG — Dependency Cycle
# =============================================================================
# This config has a circular dependency. Two resources reference each other.
#
# Your task:
#   1. Run `terraform validate` — see the cycle error
#   2. Identify which references create the cycle
#   3. Fix it so both resources can be created
#
# Don't peek at SOLUTION.md until you've tried!
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

# Resource A references Resource B
resource "local_file" "config_a" {
  filename = "${path.module}/output/config-a.txt"
  content  = "Config A depends on: ${local_file.config_b.filename}"
}

# Resource B references Resource A — CYCLE!
resource "local_file" "config_b" {
  filename = "${path.module}/output/config-b.txt"
  content  = "Config B depends on: ${local_file.config_a.filename}"
}

output "files" {
  value = [local_file.config_a.filename, local_file.config_b.filename]
}
