# =============================================================================
# BROKEN CONFIG — Version Conflict
# =============================================================================
# This config has provider version constraints that can't be satisfied.
#
# Your task:
#   1. Run `terraform init` — see the version error
#   2. Figure out which constraint is wrong
#   3. Fix the version constraints
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    # BUG: Version 1.0.0 of the random provider doesn't exist
    # (the random provider started at 2.x)
    random = {
      source  = "hashicorp/random"
      version = "= 1.0.0"
    }

    # BUG: These constraints conflict — can't be >= 3.0 AND < 2.0
    local = {
      source  = "hashicorp/local"
      version = ">= 3.0.0, < 2.0.0"
    }
  }
}

provider "random" {}
provider "local" {}

resource "random_pet" "name" {
  length = 2
}

resource "local_file" "demo" {
  filename = "${path.module}/output/version-fix.txt"
  content  = "Fixed! Pet name: ${random_pet.name.id}"
}

output "pet_name" {
  value = random_pet.name.id
}
