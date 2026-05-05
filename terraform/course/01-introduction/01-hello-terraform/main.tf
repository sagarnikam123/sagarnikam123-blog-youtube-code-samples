# =============================================================================
# Module 01 — Exercise 1: Hello Terraform
# =============================================================================
# This is the simplest possible Terraform configuration.
# It uses the "local" provider to create a file on your machine.
#
# Usage:
#   terraform init      # Download the local provider
#   terraform plan      # See what Terraform will do
#   terraform apply     # Create the file
#   terraform destroy   # Remove the file
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

# The local provider needs no configuration
provider "local" {}

# Create a simple text file
resource "local_file" "hello" {
  filename = "${path.module}/output/hello.txt"
  content  = "Hello, Terraform! This file was created by Infrastructure as Code."
}

# Show the file path after apply
output "file_path" {
  description = "Path to the created file"
  value       = local_file.hello.filename
}
