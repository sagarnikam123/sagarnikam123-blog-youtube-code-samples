# =============================================================================
# Module 09 — Exercise 1: Local Module
# =============================================================================
# Call a local module to create Docker containers.
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

# Call the docker-app module for a web server
module "web" {
  source = "./modules/docker-app"

  app_name      = "module-demo-web"
  image         = "nginx:alpine"
  internal_port = 80
  external_port = 8088

  env_vars = {
    NGINX_HOST = "localhost"
    NGINX_PORT = "80"
  }
}

# Call the same module for an API server
module "api" {
  source = "./modules/docker-app"

  app_name      = "module-demo-api"
  image         = "httpd:alpine"
  internal_port = 80
  external_port = 8089

  env_vars = {
    APP_ENV = "development"
  }
}

# Access module outputs
output "web_url" {
  value = module.web.access_url
}

output "api_url" {
  value = module.api.access_url
}

output "web_container" {
  value = module.web.container_name
}

output "api_container" {
  value = module.api.container_name
}
