# Solution — Sensitive Output

## The Fix
Mark both outputs as sensitive:

```hcl
output "database_password" {
  description = "The generated database password"
  value       = random_password.db.result
  sensitive   = true
}

output "connection_string" {
  description = "Database connection string"
  value       = "postgres://admin:${random_password.db.result}@localhost:5432/mydb"
  sensitive   = true
}
```

## The Lesson
Any output that contains or derives from a sensitive value must be marked `sensitive = true`. Terraform enforces this to prevent accidental exposure in logs and CI output. Use `terraform output -json` when you need to retrieve sensitive values programmatically.
