# =============================================================================
# Module 05 — Exercise 1: Variable Types
# =============================================================================
# Demonstrates every variable type Terraform supports.
#
# Try:
#   terraform plan
#   terraform plan -var 'app_name=myapp'
#   terraform plan -var 'tags={"team":"devops","env":"staging"}'
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

# --- String ---
variable "app_name" {
  description = "Application name"
  type        = string
  default     = "terraform-course"
}

# --- Number ---
variable "replica_count" {
  description = "Number of replicas"
  type        = number
  default     = 3
}

# --- Bool ---
variable "enable_logging" {
  description = "Enable logging"
  type        = bool
  default     = true
}

# --- List ---
variable "allowed_ports" {
  description = "List of allowed ports"
  type        = list(number)
  default     = [80, 443, 8080]
}

# --- Set (like list but no duplicates, unordered) ---
variable "environments" {
  description = "Set of environment names"
  type        = set(string)
  default     = ["dev", "staging", "prod"]
}

# --- Map ---
variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default = {
    project = "terraform-course"
    owner   = "devops-team"
  }
}

# --- Object (structured type with named attributes) ---
variable "container_config" {
  description = "Container configuration"
  type = object({
    image         = string
    internal_port = number
    external_port = number
    env_vars      = map(string)
  })
  default = {
    image         = "nginx:alpine"
    internal_port = 80
    external_port = 8080
    env_vars = {
      NODE_ENV = "development"
      LOG_LEVEL = "debug"
    }
  }
}

# --- Tuple (ordered, mixed types) ---
variable "server_spec" {
  description = "Server spec: [name, cpu_count, is_public]"
  type        = tuple([string, number, bool])
  default     = ["web-server", 4, true]
}

# --- Write all variable values to a file for inspection ---
resource "local_file" "variable_dump" {
  filename = "${path.module}/output/variables.txt"
  content  = <<-EOT
    === Variable Types Demo ===

    String:  ${var.app_name}
    Number:  ${var.replica_count}
    Bool:    ${var.enable_logging}

    List:    ${jsonencode(var.allowed_ports)}
    Set:     ${jsonencode(var.environments)}
    Map:     ${jsonencode(var.tags)}

    Object:  ${jsonencode(var.container_config)}
    Tuple:   ${jsonencode(var.server_spec)}

    --- Accessing individual elements ---
    First port:       ${var.allowed_ports[0]}
    Project tag:      ${var.tags["project"]}
    Container image:  ${var.container_config.image}
    Server name:      ${var.server_spec[0]}
  EOT
}

output "summary" {
  value = "Created variable dump at ${local_file.variable_dump.filename}"
}
