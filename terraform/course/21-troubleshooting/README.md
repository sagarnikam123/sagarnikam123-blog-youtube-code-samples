# Module 21 — Troubleshooting & Common Mistakes

## Overview

Every DevOps engineer hits the same walls when learning Terraform. This module contains **intentionally broken configurations** for you to debug. Each exercise has a broken config and a hints file — try to fix it yourself before looking at the solution.

## How to Use

```bash
cd 01-dependency-cycle

# 1. Read the README to understand the problem
# 2. Try to fix it yourself
# 3. Run terraform validate / terraform plan to check
# 4. If stuck, read HINTS.md
# 5. Only then look at SOLUTION.md
```

## Common Error Categories

| Error | Typical Cause | Quick Fix |
|-------|--------------|-----------|
| `Error: Cycle` | Two resources reference each other | Break the cycle with `depends_on` or restructure |
| `Error: Resource already exists` | Resource created outside Terraform | `terraform import` or `import {}` block |
| `Error: Provider configuration not present` | Missing or misconfigured provider | Add `required_providers` block |
| `Error: Invalid count argument` | count depends on a resource attribute | Use data source or hardcode the value |
| `Error: Unsupported attribute` | Typo in attribute name or wrong resource type | Check provider docs for correct attributes |
| `Error: No matching version` | Version constraint too strict | Relax the constraint or run `terraform init -upgrade` |
| `Error: state lock` | Previous run crashed or concurrent access | `terraform force-unlock <id>` |
| `Error: Inconsistent dependency lock` | Lock file doesn't match config | `terraform init -upgrade` |
| Plan shows destroy+create | Changed a "force new" argument | Use `moved {}` block or accept recreation |
| Sensitive value in output | Output references sensitive variable | Add `sensitive = true` to the output |
| `Error: Invalid for_each argument` | for_each value not known at plan time | Use a static map/set, not a computed value |

## Official Docs

- [Troubleshooting Terraform](https://developer.hashicorp.com/terraform/language/resources/behavior#error-handling)
- [Debugging Terraform](https://developer.hashicorp.com/terraform/internals/debugging)
- [Common Error Messages](https://developer.hashicorp.com/terraform/language/expressions/references#values-not-yet-known)

## Exercises

| # | Exercise | Error Type |
|---|----------|-----------|
| 1 | [Dependency Cycle](./01-dependency-cycle/) | `Error: Cycle` — circular references |
| 2 | [Provider Mismatch](./02-provider-mismatch/) | Missing/wrong provider config |
| 3 | [State Drift](./03-state-drift/) | Real resource changed outside Terraform |
| 4 | [Invalid For Each](./04-invalid-for-each/) | for_each with unknown values |
| 5 | [Sensitive Output](./05-sensitive-output/) | Sensitive value leaking to output |
| 6 | [Version Conflict](./06-version-conflict/) | Provider version constraints that can't be satisfied |
