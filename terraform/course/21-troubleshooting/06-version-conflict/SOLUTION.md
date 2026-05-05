# Solution — Version Conflict

## Fixed version constraints

```hcl
required_providers {
  random = {
    source  = "hashicorp/random"
    version = "~> 3.6"
  }
  local = {
    source  = "hashicorp/local"
    version = "~> 2.5"
  }
}
```

## The Lesson
- Always check the Registry for available versions before pinning
- `~> 3.6` is the safest default — allows patch updates, blocks breaking changes
- Conflicting range constraints (>= X, < Y where Y < X) are a common typo
- Run `terraform init -upgrade` after fixing constraints to re-resolve versions
