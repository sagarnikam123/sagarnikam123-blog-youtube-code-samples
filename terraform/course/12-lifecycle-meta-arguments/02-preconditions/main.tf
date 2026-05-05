# =============================================================================
# Module 12 — Exercise 2: Preconditions & Postconditions
# =============================================================================
# Validate assumptions before and after resource creation.
#
# Try:
#   terraform plan -var 'port=80'        # fails precondition
#   terraform plan -var 'port=9062'      # passes
#   terraform plan -var 'image=invalid'  # fails precondition
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

provider "docker" {}
provider "local" {}

variable "port" {
  type    = number
  default = 9062
}

variable "image" {
  type    = string
  default = "nginx:alpine"
}

variable "environment" {
  type    = string
  default = "dev"
}

resource "docker_image" "app" {
  name         = var.image
  keep_locally = true
}

resource "docker_container" "app" {
  name  = "precondition-demo"
  image = docker_image.app.image_id

  ports {
    internal = 80
    external = var.port
  }

  lifecycle {
    # Precondition: validate BEFORE creation
    precondition {
      condition     = var.port >= 1024 && var.port <= 65535
      error_message = "Port must be between 1024 and 65535 (unprivileged)."
    }

    precondition {
      condition     = can(regex("^[a-z]+:[a-z0-9.-]+$", var.image))
      error_message = "Image must be in format 'name:tag' (e.g., nginx:alpine)."
    }

    # Postcondition: validate AFTER creation
    postcondition {
      condition     = self.id != ""
      error_message = "Container was not created successfully."
    }
  }
}

# Check block — standalone validation (Terraform 1.5+)
check "container_health" {
  data "http" "health" {
    url = "http://localhost:${var.port}"
  }

  assert {
    condition     = data.http.health.status_code == 200
    error_message = "Container is not responding on port ${var.port}."
  }
}

resource "local_file" "precondition_result" {
  filename = "${path.module}/output/precondition-result.txt"
  content  = <<-EOT
    All preconditions passed!
    Container: ${docker_container.app.name}
    Port:      ${var.port}
    Image:     ${var.image}
  EOT
}

output "container_url" {
  value = "http://localhost:${var.port}"
}
