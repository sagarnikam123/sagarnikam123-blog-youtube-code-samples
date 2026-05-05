# =============================================================================
# Module 08 — Exercise 2: Import Existing Resources
# =============================================================================
# Demonstrates importing a resource that was created outside Terraform.
#
# Steps:
#   1. Create a Docker container manually:
#      docker run -d --name import-demo -p 8087:80 nginx:alpine
#
#   2. Run terraform plan — it will show the import action
#      terraform plan
#
#   3. Run terraform apply — imports the container into state
#      terraform apply
#
#   4. Now Terraform manages it! Try:
#      terraform state show docker_container.imported
#
#   5. Clean up:
#      terraform destroy
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

# The import block (Terraform 1.5+) — config-driven import
# Replace the id with the actual container ID or name after step 1
import {
  to = docker_container.imported
  id = "import-demo"
}

resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  keep_locally = true
}

# This resource definition must match the existing container
resource "docker_container" "imported" {
  name  = "import-demo"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = 8087
  }
}

output "imported_container" {
  value = docker_container.imported.name
}

output "imported_id" {
  value = docker_container.imported.id
}
