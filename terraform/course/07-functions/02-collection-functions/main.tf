# =============================================================================
# Module 07 — Exercise 2: Collection Functions
# =============================================================================
# Work with lists, maps, and sets using built-in functions.
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

variable "ports" {
  type    = list(number)
  default = [8080, 3000, 5432, 6379, 8080, 3000]
}

variable "team_a" {
  type    = map(string)
  default = {
    lead    = "Alice"
    backend = "Bob"
  }
}

variable "team_b" {
  type    = map(string)
  default = {
    frontend = "Charlie"
    devops   = "Dave"
    lead     = "Eve" # conflicts with team_a — merge takes last value
  }
}

variable "nested_list" {
  type    = list(list(string))
  default = [["a", "b"], ["c"], ["d", "e", "f"]]
}

locals {
  # Length
  port_count = length(var.ports)

  # Distinct (remove duplicates)
  unique_ports = distinct(var.ports)

  # Sort
  sorted_ports = sort([for p in var.ports : tostring(p)])

  # Reverse
  reversed = reverse(var.ports)

  # Slice
  first_three = slice(var.ports, 0, 3)

  # Contains
  has_5432 = contains(var.ports, 5432)
  has_9999 = contains(var.ports, 9999)

  # Element (wraps around)
  third_port = element(var.ports, 2)

  # Concat lists
  all_ports = concat(var.ports, [9090, 9091])

  # Flatten nested lists
  flat = flatten(var.nested_list)

  # Compact (remove empty strings)
  compacted = compact(["hello", "", "world", "", "!"])

  # Map operations
  merged_team = merge(var.team_a, var.team_b)
  team_roles  = keys(var.team_a)
  team_names  = values(var.team_a)

  # Lookup with default
  devops_person = lookup(var.team_a, "devops", "unassigned")

  # Zipmap
  services = zipmap(
    ["web", "api", "db"],
    [8080, 3000, 5432]
  )
}

resource "local_file" "collection_demo" {
  filename = "${path.module}/output/collection-functions.txt"
  content  = <<-EOT
    === Collection Functions Demo ===

    Original ports:  ${jsonencode(var.ports)}
    Count:           ${local.port_count}
    Unique:          ${jsonencode(local.unique_ports)}
    Sorted:          ${jsonencode(local.sorted_ports)}
    Reversed:        ${jsonencode(local.reversed)}
    First three:     ${jsonencode(local.first_three)}

    Contains 5432:   ${local.has_5432}
    Contains 9999:   ${local.has_9999}
    Element at [2]:  ${local.third_port}

    Concatenated:    ${jsonencode(local.all_ports)}
    Flattened:       ${jsonencode(local.flat)}
    Compacted:       ${jsonencode(local.compacted)}

    Merged team:     ${jsonencode(local.merged_team)}
    Team A roles:    ${jsonencode(local.team_roles)}
    Team A names:    ${jsonencode(local.team_names)}
    DevOps person:   ${local.devops_person}

    Zipmap result:   ${jsonencode(local.services)}
  EOT
}

output "unique_ports" {
  value = local.unique_ports
}

output "merged_team" {
  value = local.merged_team
}
