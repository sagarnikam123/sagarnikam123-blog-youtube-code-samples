# =============================================================================
# Module 13 — Exercise 1: Local Exec Provisioner
# =============================================================================
# Run local commands during resource creation and destruction.
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}
provider "null" {}

resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  keep_locally = true
}

resource "docker_container" "web" {
  name  = "provisioner-demo"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = 9070
  }

  # Run after container is created
  provisioner "local-exec" {
    command = "echo 'Container ${self.name} created with ID ${self.id}' > ${path.module}/output/create-log.txt"
  }

  # Run before container is destroyed
  provisioner "local-exec" {
    when    = destroy
    command = "echo 'Container ${self.name} is being destroyed' >> ${path.module}/output/destroy-log.txt"
  }
}

# null_resource with triggers — re-runs when trigger values change
resource "null_resource" "health_check" {
  triggers = {
    container_id = docker_container.web.id
  }

  provisioner "local-exec" {
    command = <<-EOT
      echo "Running health check..."
      sleep 2
      curl -s -o /dev/null -w "HTTP Status: %%{http_code}\n" http://localhost:9070 || echo "Container not ready yet"
    EOT
  }
}

# on_failure behavior
resource "null_resource" "might_fail" {
  provisioner "local-exec" {
    command    = "echo 'This command succeeds'"
    on_failure = continue # continue even if this fails (default is "fail")
  }
}

output "container_url" {
  value = "http://localhost:9070"
}
