# =============================================================================
# Module 28 — Exercise 3: Extensions
# =============================================================================
# Enable PostgreSQL extensions — uuid-ossp, pg_trgm, hstore, etc.
#
# Prerequisites: PostgreSQL container running
#
# After apply:
#   docker exec terraform-postgres psql -U postgres -d myapp -c "\dx"
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
variable "extensions" {
  description = "PostgreSQL extensions to enable"
  type = map(object({
    database = string
    schema   = optional(string, "public")
  }))
  default = {
    "uuid-ossp" = {
      database = "myapp"
    }
    "pg_trgm" = {
      database = "myapp"
    }
    "hstore" = {
      database = "myapp"
    }
    "citext" = {
      database = "myapp"
    }
    "pgcrypto" = {
      database = "myapp"
    }
  }
}

# --- Enable extensions using for_each ---
resource "postgresql_extension" "extensions" {
  for_each = var.extensions

  name     = each.key
  database = each.value.database
  schema   = each.value.schema
}

# --- Outputs ---
output "enabled_extensions" {
  value = [for ext in postgresql_extension.extensions : ext.name]
}

output "verify_command" {
  value = "docker exec terraform-postgres psql -U postgres -d myapp -c \"\\dx\""
}

output "usage_examples" {
  value = <<-EOT
    -- uuid-ossp: Generate UUIDs
    SELECT uuid_generate_v4();

    -- pg_trgm: Fuzzy text search
    SELECT similarity('terraform', 'terrafrom');

    -- hstore: Key-value pairs in a column
    SELECT 'key=>value'::hstore;

    -- citext: Case-insensitive text
    CREATE TABLE users (email citext UNIQUE);

    -- pgcrypto: Encryption
    SELECT crypt('password', gen_salt('bf'));
  EOT
}
