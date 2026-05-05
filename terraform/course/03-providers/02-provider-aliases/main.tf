# =============================================================================
# Module 03 — Exercise 2: Provider Aliases
# =============================================================================
# Demonstrates using multiple configurations of the same provider.
# Here we use two "local" provider configs writing to different directories.
#
# In real-world scenarios, aliases are used for:
# - Multi-region deployments (aws.us_east, aws.eu_west)
# - Multi-account setups
# - Different Docker hosts
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

# Default provider — no alias
provider "local" {}

# Aliased provider — same type, different logical identity
# (In practice, aliases differ in config like region, host, credentials)
provider "local" {
  alias = "backup"
}

resource "random_uuid" "id" {}

# Uses the default local provider
resource "local_file" "primary" {
  filename = "${path.module}/output/primary/config.txt"
  content  = "Primary config — ID: ${random_uuid.id.result}"
}

# Uses the aliased local provider
resource "local_file" "backup" {
  provider = local.backup
  filename = "${path.module}/output/backup/config.txt"
  content  = "Backup config — ID: ${random_uuid.id.result}"
}

output "primary_path" {
  value = local_file.primary.filename
}

output "backup_path" {
  value = local_file.backup.filename
}
