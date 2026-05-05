# Module 28 — PostgreSQL Provider

## Overview

Manage PostgreSQL databases, roles, schemas, grants, and extensions as code. Run PostgreSQL locally via Docker — zero cost, instant setup.

This is real DBA work that platform engineers do daily: creating databases for new services, managing role permissions, setting up schemas.

## Prerequisites

```bash
# Start PostgreSQL via Docker
docker run -d --name terraform-postgres \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=terraform \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=postgres \
  postgres:17-alpine

# Verify
docker exec terraform-postgres psql -U postgres -c "SELECT version();"
```

## Provider Configuration

```hcl
provider "postgresql" {
  host     = "localhost"
  port     = 5432
  username = "postgres"
  password = "terraform"
  sslmode  = "disable"
}
```

## Key Resources

| Resource | What It Does |
|----------|-------------|
| `postgresql_database` | Create databases |
| `postgresql_role` | Create users/roles |
| `postgresql_schema` | Create schemas within a database |
| `postgresql_grant` | Grant permissions to roles |
| `postgresql_extension` | Enable PostgreSQL extensions |
| `postgresql_default_privileges` | Set default privileges for new objects |

## Official Docs

- [PostgreSQL Provider](https://registry.terraform.io/providers/cyrilgdn/postgresql/latest/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/17/)

## Exercises

| # | Exercise | Folder |
|---|----------|--------|
| 1 | [Databases & Roles](./01-databases-roles/) | Create databases, users, and role hierarchy |
| 2 | [Schemas & Grants](./02-schemas-grants/) | Create schemas and manage fine-grained permissions |
| 3 | [Extensions & Config](./03-extensions/) | Enable extensions (uuid-ossp, pg_trgm, etc.) |
