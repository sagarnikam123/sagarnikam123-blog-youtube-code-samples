# =============================================================================
# Module 25 — Exercise 1: KV Secrets
# =============================================================================
# Write and read secrets from Vault's KV v2 secrets engine.
#
# Prerequisites:
#   vault server -dev -dev-root-token-id="root"
#   # or: docker run -d -p 8200:8200 -e VAULT_DEV_ROOT_TOKEN_ID=root hashicorp/vault
#
# After apply:
#   vault kv list secret/
#   vault kv get secret/app/database
#   vault kv get secret/app/api-keys
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    vault = {
      source  = "hashicorp/vault"
      version = "~> 4.0"
    }
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

provider "vault" {
  address = "http://127.0.0.1:8200"
  token   = "root" # dev mode only!
}

provider "random" {}
provider "local" {}

# --- Generate secrets ---
resource "random_password" "db_password" {
  length  = 32
  special = true
}

resource "random_password" "api_key" {
  length  = 48
  special = false
}

# --- Enable KV v2 secrets engine at custom path ---
resource "vault_mount" "app_secrets" {
  path        = "secret"
  type        = "kv-v2"
  description = "Application secrets"
}

# --- Write database credentials ---
resource "vault_kv_secret_v2" "database" {
  mount = vault_mount.app_secrets.path
  name  = "app/database"

  data_json = jsonencode({
    host     = "postgres.internal"
    port     = 5432
    database = "myapp"
    username = "app_user"
    password = random_password.db_password.result
  })
}

# --- Write API keys ---
resource "vault_kv_secret_v2" "api_keys" {
  mount = vault_mount.app_secrets.path
  name  = "app/api-keys"

  data_json = jsonencode({
    stripe_key     = "sk_test_${random_password.api_key.result}"
    sendgrid_key   = "SG.${substr(random_password.api_key.result, 0, 32)}"
    internal_token = random_password.api_key.result
  })
}

# --- Write application config ---
resource "vault_kv_secret_v2" "app_config" {
  mount = vault_mount.app_secrets.path
  name  = "app/config"

  data_json = jsonencode({
    environment = "development"
    log_level   = "debug"
    feature_flags = jsonencode({
      new_ui     = true
      dark_mode  = true
      beta_api   = false
    })
  })
}

# --- Read back a secret (data source) ---
data "vault_kv_secret_v2" "read_db" {
  mount = vault_mount.app_secrets.path
  name  = vault_kv_secret_v2.database.name
}

# --- Write a non-sensitive summary ---
resource "local_file" "vault_summary" {
  filename = "${path.module}/output/vault-summary.txt"
  content  = <<-EOT
    === Vault KV Secrets Summary ===

    Secrets written:
      - secret/app/database    (host, port, database, username, password)
      - secret/app/api-keys    (stripe_key, sendgrid_key, internal_token)
      - secret/app/config      (environment, log_level, feature_flags)

    Verify with:
      export VAULT_ADDR="http://127.0.0.1:8200"
      export VAULT_TOKEN="root"
      vault kv list secret/app/
      vault kv get secret/app/database
      vault kv get -field=password secret/app/database
  EOT
}

# --- Outputs ---
output "secrets_written" {
  value = [
    "secret/app/database",
    "secret/app/api-keys",
    "secret/app/config",
  ]
}

output "db_host_from_vault" {
  description = "Database host read back from Vault"
  value       = jsondecode(data.vault_kv_secret_v2.read_db.data_json)["host"]
}

output "vault_ui" {
  value = "http://127.0.0.1:8200/ui (token: root)"
}
