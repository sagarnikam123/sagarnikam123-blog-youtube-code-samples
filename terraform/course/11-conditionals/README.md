# Module 11 — Conditionals & Logic

## Conditional Expression

```hcl
condition ? true_value : false_value
```

## Common Patterns

### Toggle a resource on/off
```hcl
resource "docker_container" "monitoring" {
  count = var.enable_monitoring ? 1 : 0
  # ...
}
```

### Choose between values
```hcl
locals {
  instance_type = var.environment == "prod" ? "large" : "small"
}
```

### Conditional with for_each
```hcl
resource "local_file" "config" {
  for_each = var.create_configs ? var.environments : {}
  # ...
}
```

### Null coalescing with try()
```hcl
locals {
  port = try(var.custom_port, 8080)
}
```

## Official Docs

- [Conditional Expressions](https://developer.hashicorp.com/terraform/language/expressions/conditionals)
- [count for Conditional Resources](https://developer.hashicorp.com/terraform/language/meta-arguments/count#conditional-creation)

## Exercises

| # | Exercise | Folder |
|---|----------|--------|
| 1 | [Feature Flags](./01-feature-flags/) | Toggle resources and behaviors with booleans |
| 2 | [Environment Config](./02-environment-config/) | Different configs per environment |
