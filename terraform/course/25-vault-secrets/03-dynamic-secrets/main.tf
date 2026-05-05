# =============================================================================
# Module 25 — Exercise 3: Dynamic Secrets
# =============================================================================
# Configure Vault to generate database credentials on-demand.
# Each request gets unique, short-lived credentials.
#
# Prerequisites:
#   1. Vault dev server running
#   2. A PostgreSQL instance (use Docker):
#      docker run -d --name postgres \
#        -p 5432:5432 \
#        -e POSTGRES_PASSWORD=rootpassword \
#        -e POSTGRES_DB=myapp \
#        postgres:17-alpine
#
# After apply:
#   vault read database/creds/app-role
#   vault read database/creds/readonly-role
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    vault = {
      source  = "hashicorp/vault"
      version = "~> 4.0"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "vault" {
  address = "http://127.0.0.1:8200"
  token   = "root"
}

provider "docker" {}

# --- Deploy PostgreSQL via Docker ---
resource "docker_image" "postgres" {
  name         = "postgres:17-alpine"
  keep_locally = true
}

resource "docker_container" "postgres" {
  name  = "vault-postgres"
  image = docker_image.postgres.image_id

  ports {
    internal = 5432
    external = 5432
  }

  env = [
    "POSTGRES_PASSWORD=rootpassword",
    "POSTGRES_DB=myapp",
    "POSTGRES_USER=postgres",
  ]

  wait = true
}

# --- Enable Database Secrets Engine ---
resource "vault_mount" "database" {
  path = "database"
  type = "database"
}

# --- Configure PostgreSQL Connection ---
resource "vault_database_secret_backend_connection" "postgres" {
  backend       = vault_mount.database.path
  name          = "myapp-postgres"
  allowed_roles = ["app-role", "readonly-role"]

  postgresql {
    connection_url = "postgres://postgres:rootpassword@host.docker.internal:5432/myapp?sslmode=disable"
  }

  depends_on = [docker_container.postgres]
}

# --- Role: App (read/write, 1-hour TTL) ---
resource "vault_database_secret_backend_role" "app" {
  backend = vault_mount.database.path
  name    = "app-role"
  db_name = vault_database_secret_backend_connection.postgres.name

  creation_statements = [
    "CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}';",
    "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";",
  ]

  revocation_statements = [
    "DROP ROLE IF EXISTS \"{{name}}\";",
  ]

  default_ttl = 3600  # 1 hour
  max_ttl     = 86400 # 24 hours
}

# --- Role: Readonly (select only, 30-min TTL) ---
resource "vault_database_secret_backend_role" "readonly" {
  backend = vault_mount.database.path
  name    = "readonly-role"
  db_name = vault_database_secret_backend_connection.postgres.name

  creation_statements = [
    "CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}';",
    "GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\";",
  ]

  revocation_statements = [
    "DROP ROLE IF EXISTS \"{{name}}\";",
  ]

  default_ttl = 1800  # 30 minutes
  max_ttl     = 3600  # 1 hour
}

# --- Outputs ---
output "database_engine_path" {
  value = vault_mount.database.path
}

output "roles" {
  value = [
    vault_database_secret_backend_role.app.name,
    vault_database_secret_backend_role.readonly.name,
  ]
}

output "generate_credentials" {
  value = <<-EOT
    # Generate app credentials (read/write, 1h TTL):
    vault read database/creds/app-role

    # Generate readonly credentials (30min TTL):
    vault read database/creds/readonly-role

    # Each call generates UNIQUE credentials!
    # They auto-expire after the TTL.
  EOT
}

output "postgres_url" {
  value = "postgres://postgres:rootpassword@localhost:5432/myapp"
}
