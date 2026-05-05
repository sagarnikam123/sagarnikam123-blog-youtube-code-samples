# =============================================================================
# Module 22 — Pattern 1: Tagging Strategy
# =============================================================================
# In production, every resource needs consistent tags for:
# - Cost allocation (which team/project is spending?)
# - Ownership (who do I contact about this resource?)
# - Environment identification (is this prod or dev?)
# - Automation (auto-shutdown dev resources at night)
#
# This pattern shows how to enforce consistent tagging.
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
  }
}

provider "docker" {}
provider "local" {}

# --- Required tag variables ---
variable "project" {
  description = "Project name"
  type        = string
  default     = "terraform-course"
}

variable "environment" {
  description = "Environment (dev/staging/prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "team" {
  description = "Owning team"
  type        = string
  default     = "platform"
}

variable "cost_center" {
  description = "Cost center for billing"
  type        = string
  default     = "engineering"
}

# --- The tagging pattern: define once, use everywhere ---
locals {
  # Common tags applied to ALL resources
  common_tags = {
    project      = var.project
    environment  = var.environment
    team         = var.team
    cost_center  = var.cost_center
    managed_by   = "terraform"
    created_at   = formatdate("YYYY-MM-DD", timestamp())
  }

  # Resource-specific tags merged with common tags
  web_tags = merge(local.common_tags, {
    service = "web"
    tier    = "frontend"
  })

  api_tags = merge(local.common_tags, {
    service = "api"
    tier    = "backend"
  })
}

# --- Apply tags as container labels ---
resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  keep_locally = true
}

resource "docker_container" "web" {
  name  = "tagged-web"
  image = docker_image.nginx.image_id

  labels {
    label = "project"
    value = local.web_tags["project"]
  }

  labels {
    label = "environment"
    value = local.web_tags["environment"]
  }

  labels {
    label = "team"
    value = local.web_tags["team"]
  }

  labels {
    label = "service"
    value = local.web_tags["service"]
  }

  labels {
    label = "managed_by"
    value = local.web_tags["managed_by"]
  }

  ports {
    internal = 80
    external = 9400
  }
}

# --- Write tag report ---
resource "local_file" "tag_report" {
  filename = "${path.module}/output/tag-report.txt"
  content  = <<-EOT
    === Tagging Strategy Report ===

    Common Tags (applied to all resources):
    ${join("\n    ", [for k, v in local.common_tags : "${k}: ${v}"])}

    Web Service Tags:
    ${join("\n    ", [for k, v in local.web_tags : "${k}: ${v}"])}

    API Service Tags:
    ${join("\n    ", [for k, v in local.api_tags : "${k}: ${v}"])}

    Pattern:
    1. Define common_tags in locals
    2. Merge resource-specific tags: merge(local.common_tags, { service = "x" })
    3. Apply to every resource
    4. In cloud providers, use default_tags in the provider block
  EOT
}

output "common_tags" {
  value = local.common_tags
}

output "web_tags" {
  value = local.web_tags
}
