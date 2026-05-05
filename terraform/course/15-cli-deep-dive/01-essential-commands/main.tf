# =============================================================================
# Module 15 — Exercise 1: Essential CLI Commands
# =============================================================================
# A playground to practice all major Terraform CLI commands.
#
# Commands to try (in order):
#
#   --- Formatting & Validation ---
#   terraform fmt                    # Auto-format .tf files
#   terraform fmt -check             # Check formatting without changing
#   terraform validate               # Validate configuration syntax
#
#   --- Planning & Applying ---
#   terraform init                   # Initialize (download providers)
#   terraform plan                   # Preview changes
#   terraform plan -out=plan.tfplan  # Save plan to file
#   terraform apply plan.tfplan      # Apply saved plan
#   terraform apply -auto-approve    # Apply without confirmation
#
#   --- Inspection ---
#   terraform show                   # Show current state
#   terraform output                 # Show outputs
#   terraform output -json           # Outputs as JSON
#   terraform providers              # List providers used
#   terraform graph                  # Generate DOT graph
#   terraform graph | dot -Tpng > graph.png  # Render graph (needs graphviz)
#
#   --- Console ---
#   terraform console               # Interactive expression evaluator
#   > var.app_name
#   > length(var.tags)
#   > upper("hello")
#   > exit
#
#   --- State ---
#   terraform state list             # List resources in state
#   terraform state show random_pet.name  # Show one resource
#
#   --- Cleanup ---
#   terraform destroy                # Destroy all resources
#   terraform destroy -target=random_pet.name  # Destroy one resource
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "random" {}
provider "local" {}
provider "docker" {}

variable "app_name" {
  type    = string
  default = "cli-playground"
}

variable "tags" {
  type = map(string)
  default = {
    project = "terraform-course"
    module  = "cli-deep-dive"
  }
}

resource "random_pet" "name" {
  length = 3
}

resource "random_integer" "port" {
  min = 9100
  max = 9199
}

resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  keep_locally = true
}

resource "docker_container" "app" {
  name  = "${var.app_name}-${random_pet.name.id}"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = random_integer.port.result
  }
}

resource "local_file" "info" {
  filename = "${path.module}/output/cli-info.txt"
  content  = <<-EOT
    App:       ${var.app_name}
    Pet Name:  ${random_pet.name.id}
    Port:      ${random_integer.port.result}
    Container: ${docker_container.app.name}
    Tags:      ${jsonencode(var.tags)}
  EOT
}

output "container_name" {
  value = docker_container.app.name
}

output "access_url" {
  value = "http://localhost:${random_integer.port.result}"
}

output "pet_name" {
  value = random_pet.name.id
}
