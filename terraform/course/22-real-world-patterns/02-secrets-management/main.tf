# =============================================================================
# Module 22 — Pattern 2: Secrets Management
# =============================================================================
# NEVER hardcode secrets in .tf files. This exercise shows safe patterns.
#
# Pattern 1: Environment variables (TF_VAR_xxx)
# Pattern 2: .tfvars files (gitignored)
# Pattern 3: Generated secrets (random_password)
# Pattern 4: External secret stores (data sources)
#
# Try:
#   TF_VAR_api_key="my-real-key" terraform plan
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

provider "random" {}
provider "local" {}

# --- Pattern 1: Sensitive variable (set via TF_VAR_api_key or -var) ---
variable "api_key" {
  description = "API key — set via TF_VAR_api_key env var, never hardcode"
  type        = string
  sensitive   = true
  default     = "PLACEHOLDER-set-via-env-var"
}

# --- Pattern 2: Sensitive variable from .tfvars ---
variable "db_host" {
  description = "Database host — set in secrets.tfvars (gitignored)"
  type        = string
  default     = "localhost"
}

# --- Pattern 3: Generate secrets with Terraform ---
resource "random_password" "db_password" {
  length           = 32
  special          = true
  override_special = "!@#$%"
}

resource "random_password" "jwt_secret" {
  length  = 64
  special = false
}

# --- Pattern 4: Read from external store (simulated) ---
# In production, you'd use:
#   data "aws_secretsmanager_secret_version" "db" { ... }
#   data "vault_generic_secret" "db" { ... }
#   data "google_secret_manager_secret_version" "db" { ... }

# --- Write a non-sensitive summary ---
resource "local_file" "secrets_guide" {
  filename = "${path.module}/output/secrets-guide.txt"
  content  = <<-EOT
    === Secrets Management Patterns ===

    1. ENVIRONMENT VARIABLES (recommended for CI/CD):
       export TF_VAR_api_key="real-key-here"
       terraform apply

    2. TFVARS FILE (gitignored):
       # secrets.tfvars (in .gitignore)
       api_key = "real-key-here"
       db_host = "prod-db.example.com"

       terraform apply -var-file="secrets.tfvars"

    3. GENERATED SECRETS:
       Use random_password for passwords Terraform creates.
       Store the state file securely (encrypted remote backend).

    4. EXTERNAL SECRET STORES:
       - AWS Secrets Manager: data "aws_secretsmanager_secret_version"
       - HashiCorp Vault:     data "vault_generic_secret"
       - GCP Secret Manager:  data "google_secret_manager_secret_version"
       - Azure Key Vault:     data "azurerm_key_vault_secret"

    5. SOPS (Mozilla):
       Encrypt .tfvars files with SOPS, decrypt in CI/CD pipeline.

    NEVER DO:
       ✗ Hardcode secrets in .tf files
       ✗ Commit .tfvars with real secrets
       ✗ Print sensitive values in outputs without sensitive = true
       ✗ Store state files unencrypted with secrets in them
  EOT
}

# --- Outputs ---
output "db_password" {
  description = "Generated DB password"
  value       = random_password.db_password.result
  sensitive   = true
}

output "jwt_secret" {
  description = "Generated JWT secret"
  value       = random_password.jwt_secret.result
  sensitive   = true
}

output "guide_path" {
  value = local_file.secrets_guide.filename
}
