# =============================================================================
# Module 06 — Exercise 1: String Templates
# =============================================================================
# Demonstrates string interpolation, heredocs, and template directives.
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

variable "project_name" {
  type    = string
  default = "terraform-course"
}

variable "team_members" {
  type    = list(string)
  default = ["Alice", "Bob", "Charlie"]
}

variable "services" {
  type = map(number)
  default = {
    web = 8080
    api = 3000
    db  = 5432
  }
}

locals {
  # Simple interpolation
  greeting = "Welcome to ${var.project_name}!"

  # Heredoc with interpolation
  config = <<-EOT
    project: ${var.project_name}
    team_size: ${length(var.team_members)}
    created: ${formatdate("YYYY-MM-DD", timestamp())}
  EOT

  # Template directive: for loop in a string
  team_list = <<-EOT
    Team Members:
    %{for i, member in var.team_members~}
      ${i + 1}. ${member}
    %{endfor~}
  EOT

  # Template directive: conditional
  env_banner = <<-EOT
    %{if var.project_name == "terraform-course"~}
    === LEARNING ENVIRONMENT ===
    %{else~}
    === ${upper(var.project_name)} ===
    %{endif~}
  EOT

  # Template directive: for with map
  service_list = <<-EOT
    Services:
    %{for name, port in var.services~}
      - ${name}: localhost:${port}
    %{endfor~}
  EOT
}

resource "local_file" "templates" {
  filename = "${path.module}/output/templates.txt"
  content  = <<-EOT
    ${local.greeting}

    ${local.config}
    ${local.team_list}
    ${local.env_banner}
    ${local.service_list}
  EOT
}

output "greeting" {
  value = local.greeting
}

output "team_list" {
  value = local.team_list
}
