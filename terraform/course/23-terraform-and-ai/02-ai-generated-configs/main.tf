# =============================================================================
# Module 23 — Exercise 2: AI-Generated Configs
# =============================================================================
# Use the external data source to call Ollama and generate content.
# The AI generates infrastructure documentation and config suggestions.
#
# Prerequisites:
#   ollama serve
#   ollama pull llama3.2:1b
#   chmod +x scripts/ask-ollama.sh
#
# Usage:
#   terraform init
#   terraform apply
#   cat output/ai-nginx-config.txt
#   cat output/ai-dockerfile.txt
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    external = {
      source  = "hashicorp/external"
      version = "~> 2.3"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

provider "external" {}
provider "local" {}

variable "ollama_model" {
  description = "Ollama model to use"
  type        = string
  default     = "llama3.2:1b"
}

variable "ollama_url" {
  description = "Ollama API URL"
  type        = string
  default     = "http://localhost:11434"
}

# --- AI Task 1: Generate an Nginx config ---
data "external" "nginx_config" {
  program = ["bash", "${path.module}/scripts/ask-ollama.sh"]

  query = {
    model      = var.ollama_model
    ollama_url = var.ollama_url
    prompt     = "Generate a production-ready Nginx reverse proxy configuration that proxies /api to localhost:3000 and serves static files from /var/www/html. Include gzip compression, security headers, and rate limiting. Output ONLY the nginx.conf content, no explanations."
  }
}

# --- AI Task 2: Generate a Dockerfile ---
data "external" "dockerfile" {
  program = ["bash", "${path.module}/scripts/ask-ollama.sh"]

  query = {
    model      = var.ollama_model
    ollama_url = var.ollama_url
    prompt     = "Generate a multi-stage Dockerfile for a Node.js 24 application. Stage 1: install dependencies. Stage 2: build. Stage 3: production image using node:24-alpine. Include a non-root user, health check, and proper .dockerignore recommendations. Output ONLY the Dockerfile content."
  }
}

# --- AI Task 3: Generate Terraform best practices ---
data "external" "best_practices" {
  program = ["bash", "${path.module}/scripts/ask-ollama.sh"]

  query = {
    model      = var.ollama_model
    ollama_url = var.ollama_url
    prompt     = "List the top 10 Terraform best practices for production infrastructure. Be concise, one line per practice. Format as a numbered list."
  }
}

# --- Write AI outputs to files ---
resource "local_file" "nginx_config" {
  filename = "${path.module}/output/ai-nginx-config.txt"
  content  = <<-EOT
    === AI-Generated Nginx Config ===
    Model: ${data.external.nginx_config.result.model}
    Duration: ${data.external.nginx_config.result.duration}
    ---
    ${data.external.nginx_config.result.response}
  EOT
}

resource "local_file" "dockerfile" {
  filename = "${path.module}/output/ai-dockerfile.txt"
  content  = <<-EOT
    === AI-Generated Dockerfile ===
    Model: ${data.external.dockerfile.result.model}
    Duration: ${data.external.dockerfile.result.duration}
    ---
    ${data.external.dockerfile.result.response}
  EOT
}

resource "local_file" "best_practices" {
  filename = "${path.module}/output/ai-best-practices.txt"
  content  = <<-EOT
    === AI-Generated Terraform Best Practices ===
    Model: ${data.external.best_practices.result.model}
    Duration: ${data.external.best_practices.result.duration}
    ---
    ${data.external.best_practices.result.response}
  EOT
}

# --- Outputs ---
output "nginx_config_preview" {
  description = "First 200 chars of AI-generated Nginx config"
  value       = substr(data.external.nginx_config.result.response, 0, 200)
}

output "best_practices" {
  description = "AI-generated Terraform best practices"
  value       = data.external.best_practices.result.response
}

output "ai_model_used" {
  value = var.ollama_model
}

output "files_created" {
  value = [
    local_file.nginx_config.filename,
    local_file.dockerfile.filename,
    local_file.best_practices.filename,
  ]
}
