# =============================================================================
# Module 28 — Exercise 2: Schemas & Grants
# =============================================================================
# Create schemas and manage fine-grained permissions.
#
# Prerequisites: Exercise 01 applied (databases and roles exist)
#
# After apply:
#   docker exec terraform-postgres psql -U postgres -d myapp -c "\dn"
#   docker exec terraform-postgres psql -U postgres -d myapp -c "\dp"
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    postgresql = {
      source  = "cyrilgdn/postgresql"
      version = "~> 1.25"
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

# --- Variables ---
variable "schemas" {
  description = "Schemas to create in the myapp database"
  type = map(object({
    owner = string
  }))
  default = {
    app = {
      owner = "app_owner"
    }
    analytics = {
      owner = "app_owner"
    }
    audit = {
      owner = "app_owner"
    }
  }
}

# --- Schemas ---
resource "postgresql_schema" "schemas" {
  for_each = var.schemas

  name     = each.key
  database = "myapp"
  owner    = each.value.owner
}

# --- Grants: app_user gets full CRUD on app schema ---
resource "postgresql_grant" "app_user_schema" {
  database    = "myapp"
  role        = "app_user"
  schema      = "app"
  object_type = "schema"
  privileges  = ["USAGE", "CREATE"]

  depends_on = [postgresql_schema.schemas]
}

resource "postgresql_grant" "app_user_tables" {
  database    = "myapp"
  role        = "app_user"
  schema      = "app"
  object_type = "table"
  privileges  = ["SELECT", "INSERT", "UPDATE", "DELETE"]

  depends_on = [postgresql_schema.schemas]
}

# --- Grants: readonly_user gets SELECT only ---
resource "postgresql_grant" "readonly_schema" {
  database    = "myapp"
  role        = "readonly_user"
  schema      = "app"
  object_type = "schema"
  privileges  = ["USAGE"]

  depends_on = [postgresql_schema.schemas]
}

resource "postgresql_grant" "readonly_tables" {
  database    = "myapp"
  role        = "readonly_user"
  schema      = "app"
  object_type = "table"
  privileges  = ["SELECT"]

  depends_on = [postgresql_schema.schemas]
}

# --- Grants: readonly on analytics schema too ---
resource "postgresql_grant" "readonly_analytics_schema" {
  database    = "myapp"
  role        = "readonly_user"
  schema      = "analytics"
  object_type = "schema"
  privileges  = ["USAGE"]

  depends_on = [postgresql_schema.schemas]
}

resource "postgresql_grant" "readonly_analytics_tables" {
  database    = "myapp"
  role        = "readonly_user"
  schema      = "analytics"
  object_type = "table"
  privileges  = ["SELECT"]

  depends_on = [postgresql_schema.schemas]
}

# --- Default Privileges: auto-grant on future tables ---
resource "postgresql_default_privileges" "app_user_tables" {
  database    = "myapp"
  role        = "app_user"
  schema      = "app"
  owner       = "app_owner"
  object_type = "table"
  privileges  = ["SELECT", "INSERT", "UPDATE", "DELETE"]
}

resource "postgresql_default_privileges" "readonly_tables" {
  database    = "myapp"
  role        = "readonly_user"
  schema      = "app"
  owner       = "app_owner"
  object_type = "table"
  privileges  = ["SELECT"]
}

# --- Outputs ---
output "schemas_created" {
  value = [for s in postgresql_schema.schemas : s.name]
}

output "permission_summary" {
  value = <<-EOT
    app_user:     CRUD on app.* tables, USAGE+CREATE on app schema
    readonly_user: SELECT on app.* and analytics.* tables
    app_admin:    Inherits app_owner (full ownership)
  EOT
}

output "verify_commands" {
  value = <<-EOT
    docker exec terraform-postgres psql -U postgres -d myapp -c "\dn"
    docker exec terraform-postgres psql -U postgres -d myapp -c "\dp app.*"
    docker exec terraform-postgres psql -U postgres -d myapp -c "SELECT * FROM information_schema.role_table_grants WHERE grantee = 'app_user';"
  EOT
}
