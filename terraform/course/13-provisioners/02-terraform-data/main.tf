# =============================================================================
# Module 13 — Exercise 2: terraform_data Resource
# =============================================================================
# terraform_data is the modern replacement for null_resource (Terraform 1.4+).
# It's built-in — no provider needed.
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

variable "app_version" {
  type    = string
  default = "1.0.0"
}

resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  keep_locally = true
}

resource "docker_container" "web" {
  name  = "terraform-data-demo"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = 9071
  }
}

# --- terraform_data with triggers_replace ---
# Replaces itself when the trigger value changes
resource "terraform_data" "deploy_notifier" {
  triggers_replace = [var.app_version]

  # Store data in the resource (accessible via .output)
  input = {
    version     = var.app_version
    deployed_at = timestamp()
    container   = docker_container.web.name
  }

  provisioner "local-exec" {
    command = "echo 'Deployed version ${var.app_version} at ${timestamp()}' > ${path.module}/output/deploy.txt"
  }
}

# --- terraform_data as a simple trigger ---
resource "terraform_data" "post_deploy" {
  depends_on = [docker_container.web]

  provisioner "local-exec" {
    command = <<-EOT
      echo "Post-deploy tasks:"
      echo "  - Container: ${docker_container.web.name}"
      echo "  - URL: http://localhost:9071"
      echo "  - Version: ${var.app_version}"
    EOT
  }
}

output "deploy_info" {
  value = terraform_data.deploy_notifier.output
}

output "container_url" {
  value = "http://localhost:9071"
}
