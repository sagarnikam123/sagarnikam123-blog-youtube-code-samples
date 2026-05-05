# =============================================================================
# Module 06 — Exercise 3: For Expressions
# =============================================================================
# Transform lists and maps using for expressions.
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

variable "names" {
  type    = list(string)
  default = ["alice", "bob", "charlie", "dave"]
}

variable "services" {
  type = map(object({
    port    = number
    enabled = bool
  }))
  default = {
    web = { port = 8080, enabled = true }
    api = { port = 3000, enabled = true }
    db  = { port = 5432, enabled = false }
    cache = { port = 6379, enabled = true }
  }
}

locals {
  # List → List: uppercase all names
  upper_names = [for name in var.names : upper(name)]

  # List → List with index
  numbered_names = [for i, name in var.names : "${i + 1}. ${name}"]

  # List → List with filter
  short_names = [for name in var.names : name if length(name) <= 4]

  # Map → List: extract just the keys of enabled services
  enabled_services = [for name, config in var.services : name if config.enabled]

  # Map → Map: transform values
  service_urls = {
    for name, config in var.services : name => "http://localhost:${config.port}"
    if config.enabled
  }

  # List → Map: create a lookup
  name_lengths = { for name in var.names : name => length(name) }

  # Nested for: cartesian product
  env_service_pairs = flatten([
    for env in ["dev", "staging"] : [
      for svc in local.enabled_services : {
        key  = "${env}-${svc}"
        env  = env
        svc  = svc
      }
    ]
  ])
}

resource "local_file" "for_demo" {
  filename = "${path.module}/output/for-expressions.txt"
  content  = <<-EOT
    === For Expression Results ===

    Original names:    ${jsonencode(var.names)}
    Uppercased:        ${jsonencode(local.upper_names)}
    Numbered:          ${jsonencode(local.numbered_names)}
    Short names only:  ${jsonencode(local.short_names)}

    Enabled services:  ${jsonencode(local.enabled_services)}
    Service URLs:      ${jsonencode(local.service_urls)}
    Name lengths:      ${jsonencode(local.name_lengths)}

    Env-Service pairs: ${jsonencode(local.env_service_pairs)}
  EOT
}

output "upper_names" {
  value = local.upper_names
}

output "enabled_services" {
  value = local.enabled_services
}

output "service_urls" {
  value = local.service_urls
}
