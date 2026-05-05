# =============================================================================
# Module 03 — Exercise 3: Provider Version Constraints
# =============================================================================
# Demonstrates different version constraint syntaxes.
# Try changing the version constraints and running `terraform init` to see
# which versions Terraform selects.
#
# Experiment:
#   1. Run `terraform init` — note the versions installed
#   2. Change a version constraint (e.g., "= 3.5.0" for random)
#   3. Run `terraform init -upgrade` — see the version change
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    # Pessimistic constraint — allows 3.6.x but not 3.7.0
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6.0"
    }

    # Range constraint — between 2.4 and 2.6 (exclusive)
    local = {
      source  = "hashicorp/local"
      version = ">= 2.4.0, < 2.6.0"
    }

    # Pessimistic on minor — allows 3.x but not 4.0
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

provider "random" {}
provider "local" {}
provider "null" {}

resource "random_integer" "demo" {
  min = 1
  max = 100
}

resource "null_resource" "version_check" {
  # This triggers every time to show the random value
  triggers = {
    always = timestamp()
  }

  provisioner "local-exec" {
    command = "echo 'Random number: ${random_integer.demo.result}'"
  }
}

resource "local_file" "version_info" {
  filename = "${path.module}/output/version-info.txt"
  content  = <<-EOT
    This file was created to demonstrate provider version constraints.
    Random number generated: ${random_integer.demo.result}

    Check .terraform.lock.hcl to see exact versions installed.
    Run: terraform providers
  EOT
}

output "random_number" {
  value = random_integer.demo.result
}
