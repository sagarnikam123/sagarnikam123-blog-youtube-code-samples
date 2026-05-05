# =============================================================================
# Module 08 — Exercise 3: Moved & Removed Blocks
# =============================================================================
# Demonstrates refactoring resource names without destroying infrastructure.
#
# Steps:
#   1. First, apply the initial config (comment out moved/removed blocks)
#   2. Then rename the resource and add the moved block
#   3. Run terraform plan — see "moved" instead of destroy+create
#
# For this exercise, we simulate the workflow with comments.
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

# --- STEP 1: Original resource name ---
# resource "random_pet" "server" {
#   length = 2
# }

# --- STEP 2: Renamed resource + moved block ---
resource "random_pet" "web_server" {
  length = 2
}

# Tell Terraform: "server" was renamed to "web_server" — don't recreate it
moved {
  from = random_pet.server
  to   = random_pet.web_server
}

# --- Removed block example ---
# If you had a resource you want to stop managing but NOT destroy:
# removed {
#   from = random_pet.old_resource
#
#   lifecycle {
#     destroy = false  # keep the real resource, just remove from state
#   }
# }

resource "local_file" "moved_demo" {
  filename = "${path.module}/output/moved-demo.txt"
  content  = <<-EOT
    === Moved Block Demo ===

    The resource was renamed from random_pet.server to random_pet.web_server.
    The 'moved' block tells Terraform to update state instead of destroy+create.

    Pet name: ${random_pet.web_server.id}

    Workflow:
    1. Apply with original name (random_pet.server)
    2. Rename to random_pet.web_server + add moved block
    3. terraform plan shows "moved" — no destruction!
    4. After successful apply, you can remove the moved block
  EOT
}

output "pet_name" {
  value = random_pet.web_server.id
}
