# =============================================================================
# Module 09 — Exercise 2: Module Composition
# =============================================================================
# Compose a network module + app module together.
# The network module creates a Docker network, and the app module
# creates containers attached to that network.
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

# --- Network Module ---
module "network" {
  source = "./modules/network"

  network_name = "composed-app-net"
  subnet       = "172.28.0.0/16"
}

# --- App Module (uses network output) ---
module "frontend" {
  source = "./modules/app"

  app_name      = "composed-frontend"
  image         = "nginx:alpine"
  external_port = 8090
  network_id    = module.network.network_id
}

module "backend" {
  source = "./modules/app"

  app_name      = "composed-backend"
  image         = "httpd:alpine"
  external_port = 8091
  network_id    = module.network.network_id
}

output "network_name" {
  value = module.network.network_name
}

output "frontend_url" {
  value = module.frontend.access_url
}

output "backend_url" {
  value = module.backend.access_url
}
