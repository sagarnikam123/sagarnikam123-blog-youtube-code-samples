# =============================================================================
# Module 08 — Exercise 1: State Basics
# =============================================================================
# Create resources, then explore state with CLI commands.
#
# After `terraform apply`, try:
#   terraform state list
#   terraform state show random_pet.app
#   terraform state show docker_container.web
#   cat terraform.tfstate | python3 -m json.tool   # inspect raw state
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
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

provider "docker" {}
provider "random" {}
provider "local" {}

resource "random_pet" "app" {
  length = 2
}

resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  keep_locally = true
}

resource "docker_container" "web" {
  name  = "state-demo-${random_pet.app.id}"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = 8086
  }
}

resource "local_file" "state_info" {
  filename = "${path.module}/output/state-info.txt"
  content  = <<-EOT
    === State Demo ===
    Container: ${docker_container.web.name}
    Image:     ${docker_image.nginx.name}
    Pet Name:  ${random_pet.app.id}

    Try these commands:
      terraform state list
      terraform state show random_pet.app
      terraform state show docker_container.web
  EOT
}

output "container_name" {
  value = docker_container.web.name
}
