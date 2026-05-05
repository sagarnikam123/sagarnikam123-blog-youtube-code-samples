# Module 17 — Terragrunt

## What is Terragrunt?

Terragrunt is a thin wrapper around Terraform that provides extra tools for keeping your configurations DRY (Don't Repeat Yourself), managing remote state, and working with multiple modules.

**Version used in this course:** Terragrunt 1.0.2

## Why Terragrunt?

| Problem | Terraform Alone | With Terragrunt |
|---------|----------------|-----------------|
| Repeated backend config | Copy-paste in every module | Define once, inherit everywhere |
| Repeated provider config | Copy-paste | Generate blocks from parent |
| Module dependencies | Manual ordering | `dependency` blocks with auto-ordering |
| DRY variables | `.tfvars` per environment | Hierarchical `terragrunt.hcl` files |
| Running across modules | `cd` into each, run manually | `terragrunt run-all apply` |

## Installation

```bash
# macOS
brew install terragrunt

# Verify
terragrunt --version
# terragrunt version 1.0.2
```

## Key Concepts

### 1. `terragrunt.hcl` — The Config File
Every directory that Terragrunt manages has a `terragrunt.hcl` file.

### 2. `include` — Inherit Parent Config
```hcl
include "root" {
  path = find_in_parent_folders("root.hcl")
}
```

### 3. `dependency` — Cross-Module References
```hcl
dependency "network" {
  config_path = "../network"
}

inputs = {
  network_id = dependency.network.outputs.network_id
}
```

### 4. `generate` — Auto-Generate Terraform Files
```hcl
generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
provider "docker" {}
EOF
}
```

### 5. `run-all` — Apply Multiple Modules
```bash
terragrunt run-all plan     # plan all modules in dependency order
terragrunt run-all apply    # apply all modules
terragrunt run-all destroy  # destroy in reverse order
```

## Official Docs

- [Terragrunt Documentation](https://terragrunt.gruntwork.io/docs/)
- [Terragrunt Quick Start](https://terragrunt.gruntwork.io/docs/getting-started/quick-start/)
- [Terragrunt Configuration Reference](https://terragrunt.gruntwork.io/docs/reference/config-blocks-and-attributes/)
- [Keep Your Terraform Code DRY](https://terragrunt.gruntwork.io/docs/features/keep-your-terraform-code-dry/)
- [Execute Terraform Commands on Multiple Modules](https://terragrunt.gruntwork.io/docs/features/execute-terraform-commands-on-multiple-modules-at-once/)
- [Terragrunt Install Guide](https://terragrunt.gruntwork.io/docs/getting-started/install/)

## Exercises

| # | Exercise | Folder |
|---|----------|--------|
| 1 | [Terragrunt Basics](./01-basics/) | First terragrunt.hcl with DRY config |
| 2 | [Multi-Environment](./02-multi-env/) | Manage dev/staging/prod with Terragrunt |
| 3 | [Dependencies](./03-dependencies/) | Cross-module dependencies |
