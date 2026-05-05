# Module 16 — Testing & Validation

## Terraform Test Framework

Terraform 1.6+ includes a built-in test framework. Test files use `.tftest.hcl` extension.

### Running Tests
```bash
terraform test              # run all tests
terraform test -verbose     # verbose output
terraform test -filter=tests/main.tftest.hcl  # run specific test file
```

### Test File Structure
```hcl
# tests/main.tftest.hcl

run "test_name" {
  command = plan    # or "apply" for integration tests

  variables {
    environment = "prod"
  }

  assert {
    condition     = output.environment == "prod"
    error_message = "Expected prod environment"
  }
}
```

### Testing Validation Failures
```hcl
run "invalid_input" {
  command = plan

  variables {
    port = 80  # should fail validation
  }

  expect_failures = [
    var.port,
  ]
}
```

## Other Validation Mechanisms

### Variable Validation
```hcl
variable "port" {
  type = number
  validation {
    condition     = var.port >= 1024
    error_message = "Port must be >= 1024"
  }
}
```

### Preconditions & Postconditions
```hcl
resource "docker_container" "app" {
  lifecycle {
    precondition {
      condition     = var.image != ""
      error_message = "Image must not be empty"
    }
  }
}
```

### Check Blocks (Terraform 1.5+)
```hcl
check "health" {
  data "http" "check" {
    url = "http://localhost:8080/health"
  }

  assert {
    condition     = data.http.check.status_code == 200
    error_message = "Health check failed"
  }
}
```

## Official Docs

- [Tests](https://developer.hashicorp.com/terraform/language/tests)
- [terraform test Command](https://developer.hashicorp.com/terraform/cli/commands/test)
- [Custom Conditions — Preconditions & Postconditions](https://developer.hashicorp.com/terraform/language/expressions/custom-conditions)
- [Check Blocks](https://developer.hashicorp.com/terraform/language/checks)
- [Variable Validation](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules)

## Exercises

| # | Exercise | Folder |
|---|----------|--------|
| 1 | [Terraform Test](./01-terraform-test/) | Write and run `.tftest.hcl` tests |
