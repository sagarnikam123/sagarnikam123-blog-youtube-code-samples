# =============================================================================
# Module 02 — Exercise 1: Block Types Demo
# =============================================================================
# Demonstrates all major HCL block types in a single configuration.
# =============================================================================

# --- terraform block: settings and required providers ---
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

# --- provider block: configure providers ---
provider "local" {}
provider "random" {}

# --- variable block: declare inputs ---
variable "greeting" {
  description = "A greeting message"
  type        = string
  default     = "Hello from Terraform HCL!"
}

# --- locals block: computed local values ---
locals {
  timestamp = formatdate("YYYY-MM-DD hh:mm:ss", timestamp())
  filename  = "output/block-types-demo.txt"
}

# --- resource block: create infrastructure ---
resource "random_pet" "name" {
  length    = 2
  separator = "-"
}

resource "local_file" "demo" {
  filename = "${path.module}/${local.filename}"
  content  = <<-EOT
    ${var.greeting}
    Generated at: ${local.timestamp}
    Random pet name: ${random_pet.name.id}
  EOT
}

# --- data block: read existing data ---
data "local_file" "read_back" {
  filename = local_file.demo.filename

  depends_on = [local_file.demo]
}

# --- output block: expose values ---
output "pet_name" {
  description = "The generated random pet name"
  value       = random_pet.name.id
}

output "file_content" {
  description = "Content of the generated file"
  value       = data.local_file.read_back.content
}
