# Module 14 — Workspaces

## What are Workspaces?

Workspaces allow you to manage multiple instances of the same infrastructure with separate state files. Each workspace has its own `terraform.tfstate`.

## Commands

| Command | Purpose |
|---------|---------|
| `terraform workspace list` | List all workspaces |
| `terraform workspace new <name>` | Create a new workspace |
| `terraform workspace select <name>` | Switch to a workspace |
| `terraform workspace show` | Show current workspace |
| `terraform workspace delete <name>` | Delete a workspace |

## Using Workspaces in Config

```hcl
locals {
  workspace = terraform.workspace

  config = {
    dev     = { port = 8080, replicas = 1 }
    staging = { port = 8081, replicas = 2 }
    prod    = { port = 8082, replicas = 3 }
  }

  current = local.config[local.workspace]
}
```

## Workspaces vs Separate Directories

| Approach | Pros | Cons |
|----------|------|------|
| **Workspaces** | Same code, less duplication | Shared config, limited isolation |
| **Separate dirs** | Full isolation, different configs | Code duplication |
| **Terragrunt** | Best of both — DRY + isolation | Extra tool to learn |

> For production, many teams prefer separate directories or Terragrunt over workspaces.

## Official Docs

- [Workspaces](https://developer.hashicorp.com/terraform/language/state/workspaces)
- [Workspace CLI Commands](https://developer.hashicorp.com/terraform/cli/commands/workspace)
- [Managing Workspaces](https://developer.hashicorp.com/terraform/cli/workspaces)

## Exercises

| # | Exercise | Folder |
|---|----------|--------|
| 1 | [Workspace Basics](./01-workspace-basics/) | Create and switch between workspaces |
