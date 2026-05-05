# =============================================================================
# Module 18 — Final Project: Multi-Container Application
# =============================================================================
# Deploys a multi-container stack using reusable modules.
# Demonstrates: modules, for_each, variables, outputs, locals, lifecycle.
#
# Usage:
#   terraform init
#   terraform plan
#   terraform apply
#   terraform destroy
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
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "docker" {}
provider "local" {}
provider "random" {}

# --- Variables ---
variable "project_name" {
  description = "Project name used for naming resources"
  type        = string
  default     = "final-project"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "services" {
  description = "Map of services to deploy"
  type = map(object({
    image         = string
    external_port = number
    env_vars      = optional(map(string), {})
  }))
  default = {
    frontend = {
      image         = "nginx:alpine"
      external_port = 9300
      env_vars = {
        ROLE = "frontend"
      }
    }
    backend = {
      image         = "httpd:alpine"
      external_port = 9301
      env_vars = {
        ROLE = "backend"
      }
    }
    docs = {
      image         = "nginx:alpine"
      external_port = 9302
      env_vars = {
        ROLE = "docs"
      }
    }
  }
}

# --- Locals ---
locals {
  full_project_name = "${var.project_name}-${var.environment}"

  # Merge common env vars into each service
  common_env = {
    PROJECT     = var.project_name
    ENVIRONMENT = var.environment
  }
}

# --- Random suffix for uniqueness ---
resource "random_pet" "suffix" {
  length = 1
}

# --- Network Module ---
module "network" {
  source = "./modules/network"

  network_name = "${local.full_project_name}-net"
}

# --- App Modules (one per service) ---
module "services" {
  source   = "./modules/app"
  for_each = var.services

  app_name      = "${local.full_project_name}-${each.key}"
  image         = each.value.image
  external_port = each.value.external_port
  network_id    = module.network.network_id

  env_vars = merge(local.common_env, each.value.env_vars, {
    SERVICE_NAME = each.key
    INSTANCE_ID  = random_pet.suffix.id
  })
}

# --- Generate a deployment summary ---
resource "local_file" "deployment_summary" {
  filename = "${path.module}/output/deployment-summary.txt"
  content  = <<-EOT
    ╔══════════════════════════════════════════════════╗
    ║         DEPLOYMENT SUMMARY                       ║
    ╠══════════════════════════════════════════════════╣
    ║ Project:     ${local.full_project_name}
    ║ Environment: ${var.environment}
    ║ Network:     ${module.network.network_name}
    ║ Instance:    ${random_pet.suffix.id}
    ╠══════════════════════════════════════════════════╣
    ║ SERVICES:                                        ║
    %{for name, svc in module.services~}
    ║   ${upper(name)}: ${svc.access_url}
    %{endfor~}
    ╚══════════════════════════════════════════════════╝
  EOT
}

# --- Outputs ---
output "project_name" {
  description = "Full project name"
  value       = local.full_project_name
}

output "network" {
  description = "Docker network name"
  value       = module.network.network_name
}

output "service_urls" {
  description = "URLs for all deployed services"
  value       = { for name, svc in module.services : name => svc.access_url }
}

output "service_containers" {
  description = "Container names for all services"
  value       = { for name, svc in module.services : name => svc.container_name }
}

output "service_ips" {
  description = "Container IPs on the Docker network"
  value       = { for name, svc in module.services : name => svc.ip_address }
}
