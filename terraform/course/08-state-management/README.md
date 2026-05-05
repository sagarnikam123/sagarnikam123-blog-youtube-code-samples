# Module 08 — State Management

## What is Terraform State?

State is how Terraform maps your configuration to real-world resources. It's stored in `terraform.tfstate` (JSON file).

### Why State Matters
- **Mapping** — links config to real resources
- **Metadata** — tracks dependencies between resources
- **Performance** — caches attribute values to avoid querying every resource on every plan
- **Collaboration** — remote state enables team workflows

## State Commands

| Command | Purpose |
|---------|---------|
| `terraform state list` | List all resources in state |
| `terraform state show <addr>` | Show details of one resource |
| `terraform state pull` | Download remote state to stdout |
| `terraform state push` | Upload local state to remote |
| `terraform state rm <addr>` | Remove a resource from state (doesn't destroy it) |
| `terraform state mv <src> <dst>` | Rename a resource in state |

## Config-Driven State Operations (Terraform 1.7+)

Instead of CLI commands, use blocks in your config:

### `import` block
```hcl
import {
  to = docker_container.existing
  id = "container_id_here"
}
```

### `moved` block
```hcl
moved {
  from = docker_container.old_name
  to   = docker_container.new_name
}
```

### `removed` block
```hcl
removed {
  from = docker_container.deprecated

  lifecycle {
    destroy = false  # keep the real resource, just remove from state
  }
}
```

## Remote Backends

For team use, store state remotely:
```hcl
terraform {
  backend "s3" {
    bucket = "my-terraform-state"
    key    = "prod/terraform.tfstate"
    region = "us-east-1"
  }
}
```

> In this course we use local state since everything runs on your machine.

## Official Docs

- [State](https://developer.hashicorp.com/terraform/language/state)
- [State Command](https://developer.hashicorp.com/terraform/cli/commands/state)
- [Import](https://developer.hashicorp.com/terraform/language/import)
- [Moved Block](https://developer.hashicorp.com/terraform/language/moved)
- [Removed Block](https://developer.hashicorp.com/terraform/language/resources/syntax#removing-resources)
- [Backend Configuration](https://developer.hashicorp.com/terraform/language/backend)
- [State Locking](https://developer.hashicorp.com/terraform/language/state/locking)

## Exercises

| # | Exercise | Folder |
|---|----------|--------|
| 1 | [State Basics](./01-state-basics/) | Inspect and manipulate state |
| 2 | [Import](./02-import/) | Import existing resources into state |
| 3 | [Moved & Removed](./03-moved-removed/) | Refactor without destroying resources |
