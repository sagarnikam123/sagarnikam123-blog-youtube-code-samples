# Module 05 — Variables & Outputs

## Input Variables

Variables make your configuration reusable and dynamic.

```hcl
variable "name" {
  description = "Human-readable description"
  type        = string          # string, number, bool, list, map, object, tuple, set
  default     = "default_value" # optional — if missing, Terraform prompts
  sensitive   = false           # hide value from CLI output
  nullable    = true            # allow null values

  validation {
    condition     = length(var.name) > 0
    error_message = "Name must not be empty."
  }
}
```

## Variable Types

| Type | Example |
|------|---------|
| `string` | `"hello"` |
| `number` | `42` |
| `bool` | `true` |
| `list(string)` | `["a", "b"]` |
| `set(string)` | `toset(["a", "b"])` |
| `map(string)` | `{ key = "value" }` |
| `object({...})` | `{ name = string, port = number }` |
| `tuple([...])` | `[string, number]` |
| `any` | Accepts anything (avoid in production) |

## Setting Variable Values (Precedence: last wins)

1. Default value in `variable` block
2. Environment variable: `TF_VAR_name=value`
3. `terraform.tfvars` or `*.auto.tfvars` files
4. `-var 'name=value'` CLI flag
5. `-var-file="custom.tfvars"` CLI flag

## Output Values

```hcl
output "name" {
  description = "What this output represents"
  value       = resource_type.name.attribute
  sensitive   = false
}
```

Outputs are shown after `terraform apply` and can be queried with `terraform output`.

## Official Docs

- [Input Variables](https://developer.hashicorp.com/terraform/language/values/variables)
- [Output Values](https://developer.hashicorp.com/terraform/language/values/outputs)
- [Local Values](https://developer.hashicorp.com/terraform/language/values/locals)
- [Variable Validation](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules)
- [Type Constraints](https://developer.hashicorp.com/terraform/language/expressions/type-constraints)
- [Sensitive Variables](https://developer.hashicorp.com/terraform/language/values/variables#suppressing-values-in-cli-output)

## Exercises

| # | Exercise | Folder |
|---|----------|--------|
| 1 | [Variable Types](./01-variable-types/) | All variable types with examples |
| 2 | [Variable Validation](./02-variable-validation/) | Custom validation rules |
| 3 | [Sensitive Variables](./03-sensitive-variables/) | Handling secrets |
| 4 | [Outputs](./04-outputs/) | Output values and `terraform output` |
| 5 | [Tfvars Files](./05-tfvars/) | Using `.tfvars` files for different environments |
