# =============================================================================
# Module 23 — Exercise 3: Deploy Ollama with Docker
# =============================================================================
# Manage Ollama as Docker infrastructure with Terraform.
# Deploys Ollama server + Open WebUI (chat interface) on a shared network.
#
# This is the real-world pattern: deploying AI infrastructure as code.
#
# After apply:
#   - Ollama API: http://localhost:11434
#   - Open WebUI: http://localhost:3000
#
# Usage:
#   terraform init
#   terraform apply
#   open http://localhost:3000    # Open WebUI chat interface
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
  }
}

provider "docker" {}
provider "local" {}

# --- Variables ---
variable "ollama_image" {
  description = "Ollama Docker image"
  type        = string
  default     = "ollama/ollama:latest"
}

variable "webui_image" {
  description = "Open WebUI Docker image"
  type        = string
  default     = "ghcr.io/open-webui/open-webui:main"
}

variable "ollama_port" {
  description = "Host port for Ollama API"
  type        = number
  default     = 11434
}

variable "webui_port" {
  description = "Host port for Open WebUI"
  type        = number
  default     = 3000
}

variable "enable_webui" {
  description = "Deploy Open WebUI alongside Ollama"
  type        = bool
  default     = true
}

# --- Network ---
resource "docker_network" "ai_stack" {
  name = "ai-stack-network"
}

# --- Ollama Volume (persist models) ---
resource "docker_volume" "ollama_data" {
  name = "ollama-data"
}

# --- Ollama Server ---
resource "docker_image" "ollama" {
  name         = var.ollama_image
  keep_locally = true
}

resource "docker_container" "ollama" {
  name  = "ollama-server"
  image = docker_image.ollama.image_id

  networks_advanced {
    name = docker_network.ai_stack.id
  }

  ports {
    internal = 11434
    external = var.ollama_port
  }

  volumes {
    volume_name    = docker_volume.ollama_data.name
    container_path = "/root/.ollama"
  }

  env = [
    "OLLAMA_HOST=0.0.0.0",
  ]

  restart = "unless-stopped"
}

# --- Open WebUI (conditional) ---
resource "docker_image" "webui" {
  count = var.enable_webui ? 1 : 0

  name         = var.webui_image
  keep_locally = true
}

resource "docker_volume" "webui_data" {
  count = var.enable_webui ? 1 : 0
  name  = "open-webui-data"
}

resource "docker_container" "webui" {
  count = var.enable_webui ? 1 : 0

  name  = "open-webui"
  image = docker_image.webui[0].image_id

  networks_advanced {
    name = docker_network.ai_stack.id
  }

  ports {
    internal = 8080
    external = var.webui_port
  }

  volumes {
    volume_name    = docker_volume.webui_data[0].name
    container_path = "/app/backend/data"
  }

  env = [
    "OLLAMA_BASE_URL=http://ollama-server:11434",
    "WEBUI_AUTH=false",
  ]

  restart = "unless-stopped"

  depends_on = [docker_container.ollama]
}

# --- Deployment summary ---
resource "local_file" "ai_stack_info" {
  filename = "${path.module}/output/ai-stack-info.txt"
  content  = <<-EOT
    ╔══════════════════════════════════════════════════╗
    ║           AI STACK DEPLOYMENT                     ║
    ╠══════════════════════════════════════════════════╣
    ║ Ollama API:   http://localhost:${var.ollama_port}            ║
    %{if var.enable_webui~}
    ║ Open WebUI:   http://localhost:${var.webui_port}              ║
    %{endif~}
    ║ Network:      ${docker_network.ai_stack.name}
    ╠══════════════════════════════════════════════════╣
    ║ NEXT STEPS:                                      ║
    ║   1. Pull a model:                               ║
    ║      docker exec ollama-server ollama pull llama3.2:1b  ║
    ║   2. Test the API:                               ║
    ║      curl http://localhost:${var.ollama_port}/api/tags          ║
    %{if var.enable_webui~}
    ║   3. Open the chat UI:                           ║
    ║      open http://localhost:${var.webui_port}                    ║
    %{endif~}
    ╚══════════════════════════════════════════════════╝
  EOT
}

# --- Outputs ---
output "ollama_url" {
  description = "Ollama API URL"
  value       = "http://localhost:${var.ollama_port}"
}

output "webui_url" {
  description = "Open WebUI URL"
  value       = var.enable_webui ? "http://localhost:${var.webui_port}" : "disabled"
}

output "network" {
  value = docker_network.ai_stack.name
}

output "pull_model_command" {
  description = "Run this to pull a model into the Ollama container"
  value       = "docker exec ollama-server ollama pull llama3.2:1b"
}

output "test_api_command" {
  description = "Test the Ollama API"
  value       = "curl http://localhost:${var.ollama_port}/api/tags"
}
