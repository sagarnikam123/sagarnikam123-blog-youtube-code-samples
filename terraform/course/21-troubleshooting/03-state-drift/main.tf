# =============================================================================
# EXERCISE — State Drift
# =============================================================================
# Simulate state drift: a resource is changed outside Terraform.
#
# Steps:
#   1. terraform init && terraform apply -auto-approve
#   2. Manually modify the created file:
#      echo "MODIFIED OUTSIDE TERRAFORM" > output/managed-file.txt
#   3. Run terraform plan — see the drift detected
#   4. Decide: apply to restore, or import the change?
#
# This teaches you how Terraform detects and handles drift.
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

variable "content" {
  type    = string
  default = "This file is managed by Terraform. Do not edit manually."
}

resource "local_file" "managed" {
  filename = "${path.module}/output/managed-file.txt"
  content  = var.content
}

output "file_path" {
  value = local_file.managed.filename
}

output "expected_content" {
  value = var.content
}
