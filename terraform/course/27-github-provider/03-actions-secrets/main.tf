# =============================================================================
# Module 27 — Exercise 3: Actions Secrets & Webhooks
# =============================================================================
# Manage GitHub Actions secrets and repository webhooks.
# Secrets are encrypted — Terraform can set them but never read them back.
#
# Note: This creates real resources on GitHub.
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "github" {}
provider "random" {}

# --- Create a repo ---
resource "github_repository" "app" {
  name        = "terraform-secrets-demo"
  description = "Demo: Actions secrets managed by Terraform"
  visibility  = "public"
  auto_init   = true
}

# --- Generate secrets ---
resource "random_password" "db_password" {
  length  = 32
  special = false
}

resource "random_password" "api_key" {
  length  = 48
  special = false
}

# --- Actions Secrets ---
resource "github_actions_secret" "db_password" {
  repository      = github_repository.app.name
  secret_name     = "DATABASE_PASSWORD"
  plaintext_value = random_password.db_password.result
}

resource "github_actions_secret" "api_key" {
  repository      = github_repository.app.name
  secret_name     = "API_KEY"
  plaintext_value = random_password.api_key.result
}

resource "github_actions_secret" "deploy_env" {
  repository      = github_repository.app.name
  secret_name     = "DEPLOY_ENVIRONMENT"
  plaintext_value = "production"
}

# --- Actions Variables (non-secret, visible in logs) ---
resource "github_actions_variable" "app_name" {
  repository    = github_repository.app.name
  variable_name = "APP_NAME"
  value         = "terraform-secrets-demo"
}

resource "github_actions_variable" "region" {
  repository    = github_repository.app.name
  variable_name = "AWS_REGION"
  value         = "ap-south-1"
}

# --- Webhook ---
resource "github_repository_webhook" "deploy" {
  repository = github_repository.app.name

  configuration {
    url          = "https://example.com/webhook/deploy"
    content_type = "json"
    insecure_ssl = false
  }

  active = true
  events = ["push", "pull_request"]
}

# --- Outputs ---
output "repository_url" {
  value = github_repository.app.html_url
}

output "secrets_created" {
  value = [
    "DATABASE_PASSWORD",
    "API_KEY",
    "DEPLOY_ENVIRONMENT",
  ]
}

output "variables_created" {
  value = [
    "APP_NAME",
    "AWS_REGION",
  ]
}

output "webhook_url" {
  value = github_repository_webhook.deploy.configuration[0].url
}

output "note" {
  value = "Secrets are write-only — GitHub encrypts them. You can't read them back via API or Terraform."
}
