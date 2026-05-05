# Module 12 — Lifecycle & Meta-Arguments

## Meta-Arguments

Meta-arguments are special arguments available on every resource:

| Meta-Argument | Purpose |
|---------------|---------|
| `depends_on` | Explicit dependency ordering |
| `count` | Create multiple instances by number |
| `for_each` | Create instances from a map or set |
| `provider` | Select a non-default provider config |
| `lifecycle` | Customize resource lifecycle behavior |

## Lifecycle Block

```hcl
resource "docker_container" "app" {
  # ...

  lifecycle {
    create_before_destroy = true   # Create new before destroying old
    prevent_destroy       = true   # Block terraform destroy
    ignore_changes        = [env]  # Don't track changes to env
    replace_triggered_by  = [      # Force replacement when these change
      null_resource.trigger.id
    ]
  }
}
```

### Lifecycle Rules

| Rule | Effect |
|------|--------|
| `create_before_destroy` | New resource created before old one is destroyed (zero-downtime) |
| `prevent_destroy` | `terraform destroy` will error if this resource would be destroyed |
| `ignore_changes` | Terraform ignores changes to specified attributes |
| `replace_triggered_by` | Force resource replacement when referenced resources change |

## Preconditions & Postconditions

```hcl
resource "docker_container" "app" {
  # ...

  lifecycle {
    precondition {
      condition     = var.port > 1024
      error_message = "Port must be > 1024"
    }

    postcondition {
      condition     = self.id != ""
      error_message = "Container was not created"
    }
  }
}
```

## Official Docs

- [Lifecycle Meta-Argument](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle)
- [Preconditions & Postconditions](https://developer.hashicorp.com/terraform/language/expressions/custom-conditions#preconditions-and-postconditions)
- [Check Blocks](https://developer.hashicorp.com/terraform/language/checks)
- [depends_on](https://developer.hashicorp.com/terraform/language/meta-arguments/depends_on)
- [provider Meta-Argument](https://developer.hashicorp.com/terraform/language/meta-arguments/resource-provider)

## Exercises

| # | Exercise | Folder |
|---|----------|--------|
| 1 | [Lifecycle Rules](./01-lifecycle-rules/) | create_before_destroy, prevent_destroy, ignore_changes |
| 2 | [Preconditions & Postconditions](./02-preconditions/) | Validate before and after resource creation |
