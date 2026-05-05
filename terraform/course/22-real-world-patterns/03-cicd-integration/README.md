# Pattern 3 — CI/CD Integration

## Overview

In production, nobody runs `terraform apply` from their laptop. Infrastructure changes go through a CI/CD pipeline:

```
Developer → PR → fmt + validate + plan → Review → Merge → Apply
```

## Files in This Folder

| File | Purpose |
|------|---------|
| `github-actions-terraform.yml` | GitHub Actions workflow (copy to `.github/workflows/`) |

## Pipeline Stages

### On Pull Request
1. **Format check** — `terraform fmt -check` (fail if unformatted)
2. **Validate** — `terraform validate` (catch syntax errors)
3. **Plan** — `terraform plan` (post output as PR comment)
4. **Review** — Team reviews the plan diff

### On Merge to Main
5. **Apply** — `terraform apply -auto-approve` (with environment protection)

## Best Practices

- **Never apply from laptops** — all changes through CI/CD
- **Plan on PR, apply on merge** — review before deploying
- **Use remote state** — S3, GCS, or Terraform Cloud
- **Lock state** — DynamoDB for S3, built-in for Terraform Cloud
- **Pin Terraform version** — same version in CI as local dev
- **Use `-out=plan.tfplan`** — ensure apply matches the reviewed plan
- **Protect the main branch** — require PR reviews
- **Use environment protection rules** — manual approval for prod
