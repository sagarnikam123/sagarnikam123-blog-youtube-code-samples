# =============================================================================
# Module 28 — Exercise 1: Databases & Roles
# =============================================================================
# Create databases and roles with a proper hierarchy.
#
# Prerequisites:
#   docker run -d --name terraform-postgres \
#     -p 5432:5432 \
#     -e POSTGRES_PASSWORD=terraform \
#     -e POSTGRES_USER=postgres \
#     postgres:17-alpine
#
# After apply:
#   docker exec terraform-postgres psql -U postgres -c "\l"     # list databases
#   docker exec terraform-postgres psql -U postgres -c "\du"    # list roles
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    postgresql = {
      source  = "cyrilgdn/postgresql"
      version = "~> 1.25"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "postgresql" {
  host     = "localhost"
  port     = 5432
  username = "postgres"
  password = "terraform"
  sslmode  = "disable"
}

provider "random" {}

# --- Generate passwords for roles ---
resource "random_password" "app_password" {
  length  = 24
  special = false
}

resource "random_password" "readonly_password" {
  length  = 24
  special = false
}

# --- Databases ---
resource "postgresql_database" "app" {
  name              = "myapp"
  owner             = postgresql_role.app_owner.name
  encoding          = "UTF8"
  lc_collate        = "en_US.UTF-8"
  lc_ctype          = "en_US.UTF-8"
  connection_limit  = 100
  allow_connections = true
}

resource "postgresql_database" "analytics" {
  name              = "analytics"
  owner             = postgresql_role.app_owner.name
  encoding          = "UTF8"
  connection_limit  = 50
  allow_connections = true
}

# --- Role Hierarchy ---
# Parent role (no login) — owns the databases
resource "postgresql_role" "app_owner" {
  name     = "app_owner"
  login    = false
  roles    = []
}

# Application role (login) — used by the app
resource "postgresql_role" "app_user" {
  name     = "app_user"
  login    = true
  password = random_password.app_password.result
  roles    = [postgresql_role.app_owner.name]

  connection_limit = 20
}

# Read-only role (login) — used for reporting
resource "postgresql_role" "readonly" {
  name     = "readonly_user"
  login    = true
  password = random_password.readonly_password.result

  connection_limit = 10
}

# Admin role (login) — for migrations
resource "postgresql_role" "admin" {
  name            = "app_admin"
  login           = true
  password        = "admin_password_change_me"
  superuser       = false
  create_database = false
  create_role     = false
  roles           = [postgresql_role.app_owner.name]
}

# --- Outputs ---
output "databases" {
  value = [
    postgresql_database.app.name,
    postgresql_database.analytics.name,
  ]
}

output "roles" {
  value = [
    postgresql_role.app_owner.name,
    postgresql_role.app_user.name,
    postgresql_role.readonly.name,
    postgresql_role.admin.name,
  ]
}

output "app_user_password" {
  value     = random_password.app_password.result
  sensitive = true
}

output "verify_commands" {
  value = <<-EOT
    docker exec terraform-postgres psql -U postgres -c "\l"
    docker exec terraform-postgres psql -U postgres -c "\du"
    docker exec terraform-postgres psql -U app_user -d myapp -c "SELECT current_user, current_database();"
  EOT
}
