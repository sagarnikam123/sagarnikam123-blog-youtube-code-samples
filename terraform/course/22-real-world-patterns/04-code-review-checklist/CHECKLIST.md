# Terraform Code Review Checklist

Use this checklist when reviewing Terraform PRs. Not every item applies to every PR — use judgment.

---

## Security

- [ ] No secrets hardcoded in `.tf` files
- [ ] Sensitive variables marked `sensitive = true`
- [ ] Sensitive outputs marked `sensitive = true`
- [ ] No `*.tfvars` with real secrets committed
- [ ] Service account / IAM permissions follow least privilege
- [ ] State file stored in encrypted remote backend
- [ ] No `0.0.0.0/0` ingress rules without justification

## State & Lifecycle

- [ ] Resources renamed? → `moved {}` block present (no destroy+create)
- [ ] Resources removed? → `removed {}` block or explicit `terraform state rm`
- [ ] Existing resources imported? → `import {}` block present
- [ ] `prevent_destroy` on critical resources (databases, storage)
- [ ] `create_before_destroy` where zero-downtime matters
- [ ] No `-target` usage in CI/CD (full plans only)

## Variables & Types

- [ ] All variables have `description`
- [ ] All variables have explicit `type`
- [ ] Validation rules on variables that accept user input
- [ ] Sensible defaults (or no default to force explicit setting)
- [ ] No `any` type — use specific types

## Naming & Style

- [ ] `terraform fmt` passes
- [ ] Resource names are descriptive (`web_server` not `res1`)
- [ ] Files follow convention: `main.tf`, `variables.tf`, `outputs.tf`
- [ ] No commented-out code (use version control instead)
- [ ] Consistent naming: `snake_case` for resources, `kebab-case` for names

## Dependencies

- [ ] Provider versions pinned (`~> X.Y` not `>= X.Y`)
- [ ] Terraform version pinned (`required_version`)
- [ ] No unnecessary `depends_on` (prefer implicit dependencies)
- [ ] Module versions pinned for registry modules

## Modules

- [ ] Module does one thing well
- [ ] Module has `README.md` with usage example
- [ ] Module inputs validated
- [ ] Module outputs documented with `description`
- [ ] No hardcoded values — everything parameterized

## Plan Review

- [ ] Plan output reviewed — no unexpected destroys
- [ ] Resource count matches expectations
- [ ] No "forces replacement" on resources that shouldn't be recreated
- [ ] Drift detected? → Investigate before applying

## Testing

- [ ] `terraform validate` passes
- [ ] `terraform plan` succeeds
- [ ] `.tftest.hcl` tests pass (if present)
- [ ] Tested with different variable values (dev, staging, prod)

---

## Quick Commands for Reviewers

```bash
# Check formatting
terraform fmt -check -recursive

# Validate
terraform init -backend=false && terraform validate

# Plan
terraform plan -var-file="environments/dev.tfvars"

# Run tests
terraform test -verbose
```
