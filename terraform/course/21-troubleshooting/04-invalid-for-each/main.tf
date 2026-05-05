# =============================================================================
# BROKEN CONFIG — Invalid for_each
# =============================================================================
# This config tries to use for_each with a value that isn't known at plan time.
#
# Your task:
#   1. Run `terraform plan` — see the error
#   2. Understand WHY for_each can't use computed values
#   3. Fix it
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

# This generates a random number — not known until apply
resource "random_integer" "count" {
  min = 1
  max = 5
}

# BUG: for_each depends on a value that isn't known at plan time
# Terraform needs to know the for_each keys during planning
resource "local_file" "configs" {
  for_each = toset([for i in range(random_integer.count.result) : "config-${i}"])

  filename = "${path.module}/output/${each.key}.txt"
  content  = "Config file: ${each.key}"
}

output "files" {
  value = [for f in local_file.configs : f.filename]
}
