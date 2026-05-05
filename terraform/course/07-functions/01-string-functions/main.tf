# =============================================================================
# Module 07 — Exercise 1: String Functions
# =============================================================================
# Practice string functions. Run `terraform console` to experiment live.
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

variable "raw_name" {
  type    = string
  default = "  My Terraform Project  "
}

variable "csv_data" {
  type    = string
  default = "web,api,worker,scheduler"
}

variable "url" {
  type    = string
  default = "https://example.com/api/v1/users"
}

locals {
  # Trimming
  trimmed = trimspace(var.raw_name)

  # Case conversion
  upper_name = upper(local.trimmed)
  lower_name = lower(local.trimmed)
  title_name = title(lower(local.trimmed))

  # Split and join
  services     = split(",", var.csv_data)
  services_str = join(" | ", local.services)

  # Replace
  slug = replace(replace(lower(local.trimmed), " ", "-"), "--", "-")

  # Substring
  first_five = substr(local.trimmed, 0, 5)

  # Format
  formatted = format("Project: %-30s | Services: %d", local.trimmed, length(local.services))

  # Regex
  domain = regex("https?://([^/]+)", var.url)[0]

  # Prefix/suffix
  has_https = startswith(var.url, "https")
  is_users  = endswith(var.url, "/users")

  # String length
  name_length = length(local.trimmed)
}

resource "local_file" "string_demo" {
  filename = "${path.module}/output/string-functions.txt"
  content  = <<-EOT
    === String Functions Demo ===

    Raw input:     "${var.raw_name}"
    Trimmed:       "${local.trimmed}"
    Upper:         "${local.upper_name}"
    Lower:         "${local.lower_name}"
    Title:         "${local.title_name}"

    CSV split:     ${jsonencode(local.services)}
    Joined:        "${local.services_str}"

    Slug:          "${local.slug}"
    First 5:       "${local.first_five}"
    Formatted:     "${local.formatted}"

    Domain:        "${local.domain}"
    Has HTTPS:     ${local.has_https}
    Ends /users:   ${local.is_users}
    Name length:   ${local.name_length}
  EOT
}

output "slug" {
  value = local.slug
}

output "domain" {
  value = local.domain
}

output "services" {
  value = local.services
}
