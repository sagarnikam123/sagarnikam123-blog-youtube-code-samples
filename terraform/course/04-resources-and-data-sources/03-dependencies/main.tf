# =============================================================================
# Module 04 — Exercise 3: Dependencies
# =============================================================================
# Demonstrates implicit dependencies (via references) and
# explicit dependencies (via depends_on).
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
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}
provider "local" {}
provider "null" {}

# Step 1: Pull image (no dependencies)
resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  keep_locally = true
}

# Step 2: Create network (no dependencies)
resource "docker_network" "demo" {
  name = "dependency-demo-net"
}

# Step 3: Run container — IMPLICIT dependency on image and network
resource "docker_container" "web" {
  name  = "dependency-demo"
  image = docker_image.nginx.image_id # implicit dep on docker_image.nginx

  networks_advanced {
    name = docker_network.demo.id # implicit dep on docker_network.demo
  }

  ports {
    internal = 80
    external = 8083
  }
}

# Step 4: Write a log file — EXPLICIT dependency
# There's no attribute reference to the container here,
# but we want this to run AFTER the container is created.
resource "local_file" "deploy_log" {
  filename = "${path.module}/output/deploy-log.txt"
  content  = "Deployment completed at ${timestamp()}"

  depends_on = [docker_container.web] # explicit dependency
}

# Step 5: null_resource with explicit dependency — runs after everything
resource "null_resource" "health_check" {
  depends_on = [docker_container.web]

  triggers = {
    container_id = docker_container.web.id
  }

  provisioner "local-exec" {
    command = "echo 'Health check: container ${docker_container.web.name} is running'"
  }
}

output "dependency_order" {
  description = "Resources are created in this order due to dependencies"
  value       = "image → network → container → [deploy_log, health_check]"
}
