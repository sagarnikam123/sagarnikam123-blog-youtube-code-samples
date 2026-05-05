# =============================================================================
# Module 12 — Exercise 1: Lifecycle Rules
# =============================================================================
# Demonstrates lifecycle meta-arguments.
#
# Experiments:
#   1. Apply, then change the container name → see create_before_destroy
#   2. Try `terraform destroy` → see prevent_destroy error
#   3. Manually change env vars in Docker → plan shows no changes (ignore_changes)
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}
provider "random" {}
provider "null" {}

resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  keep_locally = true
}

# --- create_before_destroy ---
# When this container needs replacement, the new one is created
# before the old one is destroyed (useful for zero-downtime deploys)
resource "docker_container" "web" {
  name  = "lifecycle-web"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = 9060
  }

  env = [
    "VERSION=1.0",
    "UPDATED_AT=${timestamp()}", # changes every apply
  ]

  lifecycle {
    create_before_destroy = true
    ignore_changes        = [env] # ignore env changes after creation
  }
}

# --- prevent_destroy ---
# Uncomment prevent_destroy, apply, then try `terraform destroy`
# It will fail with an error protecting this resource.
resource "random_pet" "important" {
  length = 3

  lifecycle {
    # Uncomment to test:
    # prevent_destroy = true
  }
}

# --- replace_triggered_by ---
# This container is replaced whenever the trigger changes
resource "null_resource" "deploy_trigger" {
  triggers = {
    version = "v1.0.0" # Change this to trigger replacement
  }
}

resource "docker_container" "api" {
  name  = "lifecycle-api"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = 9061
  }

  lifecycle {
    replace_triggered_by = [null_resource.deploy_trigger]
  }
}

output "web_url" {
  value = "http://localhost:9060"
}

output "api_url" {
  value = "http://localhost:9061"
}

output "important_pet" {
  value = random_pet.important.id
}
