# Module 15 — Terraform CLI Deep Dive

## Command Reference

### Core Workflow
| Command | Purpose |
|---------|---------|
| `terraform init` | Initialize working directory, download providers |
| `terraform plan` | Preview changes |
| `terraform apply` | Apply changes |
| `terraform destroy` | Destroy all managed resources |

### Formatting & Validation
| Command | Purpose |
|---------|---------|
| `terraform fmt` | Auto-format `.tf` files to canonical style |
| `terraform fmt -check` | Check formatting without modifying |
| `terraform fmt -recursive` | Format all subdirectories |
| `terraform validate` | Validate syntax and internal consistency |

### Inspection
| Command | Purpose |
|---------|---------|
| `terraform show` | Show current state or a saved plan |
| `terraform output` | Show output values |
| `terraform output -json` | Outputs in JSON format |
| `terraform output -raw <name>` | Raw value (no quotes) |
| `terraform providers` | List providers in use |
| `terraform graph` | Generate dependency graph (DOT format) |
| `terraform console` | Interactive expression evaluator |

### State Management
| Command | Purpose |
|---------|---------|
| `terraform state list` | List all resources in state |
| `terraform state show <addr>` | Show one resource's attributes |
| `terraform state mv <src> <dst>` | Rename a resource in state |
| `terraform state rm <addr>` | Remove from state (doesn't destroy) |
| `terraform state pull` | Download remote state |
| `terraform state push` | Upload state to remote |

### Advanced
| Command | Purpose |
|---------|---------|
| `terraform plan -out=plan.tfplan` | Save plan to file |
| `terraform apply plan.tfplan` | Apply a saved plan |
| `terraform apply -target=<addr>` | Apply only one resource |
| `terraform destroy -target=<addr>` | Destroy only one resource |
| `terraform apply -replace=<addr>` | Force recreation of a resource |
| `terraform apply -auto-approve` | Skip confirmation prompt |
| `terraform force-unlock <id>` | Release a stuck state lock |
| `terraform test` | Run test files (`.tftest.hcl`) |

## Official Docs

- [CLI Commands Overview](https://developer.hashicorp.com/terraform/cli/commands)
- [terraform init](https://developer.hashicorp.com/terraform/cli/commands/init)
- [terraform plan](https://developer.hashicorp.com/terraform/cli/commands/plan)
- [terraform apply](https://developer.hashicorp.com/terraform/cli/commands/apply)
- [terraform destroy](https://developer.hashicorp.com/terraform/cli/commands/destroy)
- [terraform fmt](https://developer.hashicorp.com/terraform/cli/commands/fmt)
- [terraform validate](https://developer.hashicorp.com/terraform/cli/commands/validate)
- [terraform console](https://developer.hashicorp.com/terraform/cli/commands/console)
- [terraform graph](https://developer.hashicorp.com/terraform/cli/commands/graph)
- [terraform output](https://developer.hashicorp.com/terraform/cli/commands/output)
- [terraform state](https://developer.hashicorp.com/terraform/cli/commands/state)

## Exercises

| # | Exercise | Folder |
|---|----------|--------|
| 1 | [Essential Commands](./01-essential-commands/) | Practice all major CLI commands |
