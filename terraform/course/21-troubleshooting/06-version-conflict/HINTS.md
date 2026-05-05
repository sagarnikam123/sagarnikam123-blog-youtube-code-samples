# Hints — Version Conflict

## Hint 1
Check the Terraform Registry for available versions:
- https://registry.terraform.io/providers/hashicorp/random/latest
- https://registry.terraform.io/providers/hashicorp/local/latest

## Hint 2
The random provider has no version 1.0.0. Use `~> 3.6` for the latest 3.x.

## Hint 3
The local provider constraint `>= 3.0.0, < 2.0.0` is impossible — nothing can be both >= 3 and < 2. Use `~> 2.5` for the latest 2.x.
