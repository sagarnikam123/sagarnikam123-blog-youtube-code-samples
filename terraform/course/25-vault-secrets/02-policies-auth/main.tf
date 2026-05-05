# =============================================================================
# Module 25 — Exercise 2: Policies & AppRole Auth
# =============================================================================
# Create Vault policies and set up AppRole authentication.
# AppRole is the standard way applications authenticate to Vault.
#
# After apply:
#   vault policy list
#   vault policy read app-readonly
#   vault read auth/approle/role/web-app
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    vault = {
      source  = "hashicorp/vault"
      version = "~> 4.0"
    }
  }
}

provider "vault" {
  address = "http://127.0.0.1:8200"
  token   = "root"
}

# --- Policy: Read-only access to app secrets ---
resource "vault_policy" "app_readonly" {
  name = "app-readonly"

  policy = <<-EOT
    # Read app secrets
    path "secret/data/app/*" {
      capabilities = ["read", "list"]
    }

    # List secret paths
    path "secret/metadata/app/*" {
      capabilities = ["list"]
    }
  EOT
}

# --- Policy: Full access to app secrets ---
resource "vault_policy" "app_admin" {
  name = "app-admin"

  policy = <<-EOT
    # Full CRUD on app secrets
    path "secret/data/app/*" {
      capabilities = ["create", "read", "update", "delete", "list"]
    }

    path "secret/metadata/app/*" {
      capabilities = ["list", "read", "delete"]
    }

    # Manage own token
    path "auth/token/renew-self" {
      capabilities = ["update"]
    }
  EOT
}

# --- Policy: CI/CD pipeline (limited write) ---
resource "vault_policy" "cicd" {
  name = "cicd-pipeline"

  policy = <<-EOT
    # Read secrets for deployment
    path "secret/data/app/*" {
      capabilities = ["read"]
    }

    # Read infrastructure secrets
    path "secret/data/infra/*" {
      capabilities = ["read"]
    }
  EOT
}

# --- Enable AppRole auth method ---
resource "vault_auth_backend" "approle" {
  type = "approle"
  path = "approle"
}

# --- AppRole: Web Application ---
resource "vault_approle_auth_backend_role" "web_app" {
  backend   = vault_auth_backend.approle.path
  role_name = "web-app"

  token_policies = [
    vault_policy.app_readonly.name,
  ]

  token_ttl     = 3600  # 1 hour
  token_max_ttl = 14400 # 4 hours

  # Security settings
  secret_id_num_uses = 0  # unlimited
  token_num_uses     = 0  # unlimited
}

# --- AppRole: CI/CD Pipeline ---
resource "vault_approle_auth_backend_role" "cicd" {
  backend   = vault_auth_backend.approle.path
  role_name = "cicd-pipeline"

  token_policies = [
    vault_policy.cicd.name,
  ]

  token_ttl     = 1800 # 30 minutes
  token_max_ttl = 3600 # 1 hour

  # Stricter: secret_id can only be used once
  secret_id_num_uses = 1
}

# --- Get the Role ID (needed for authentication) ---
data "vault_approle_auth_backend_role_id" "web_app" {
  backend   = vault_auth_backend.approle.path
  role_name = vault_approle_auth_backend_role.web_app.role_name
}

# --- Outputs ---
output "policies" {
  value = [
    vault_policy.app_readonly.name,
    vault_policy.app_admin.name,
    vault_policy.cicd.name,
  ]
}

output "approle_roles" {
  value = [
    vault_approle_auth_backend_role.web_app.role_name,
    vault_approle_auth_backend_role.cicd.role_name,
  ]
}

output "web_app_role_id" {
  description = "Role ID for the web-app AppRole (use with secret_id to authenticate)"
  value       = data.vault_approle_auth_backend_role_id.web_app.role_id
}

output "auth_example" {
  value = <<-EOT
    # Generate a secret_id:
    vault write -f auth/approle/role/web-app/secret-id

    # Authenticate with role_id + secret_id:
    vault write auth/approle/login \
      role_id="${data.vault_approle_auth_backend_role_id.web_app.role_id}" \
      secret_id="<secret_id_from_above>"
  EOT
}
