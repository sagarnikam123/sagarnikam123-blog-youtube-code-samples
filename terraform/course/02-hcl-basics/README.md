# Module 02 — HCL Basics & Configuration Syntax

## What is HCL?

HCL (HashiCorp Configuration Language) is the declarative language Terraform uses. It's designed to be human-readable while being machine-parseable.

## File Structure

```
project/
├── main.tf          # Primary resource definitions
├── variables.tf     # Input variable declarations
├── outputs.tf       # Output value declarations
├── providers.tf     # Provider configuration
├── terraform.tf     # Terraform settings (required_version, backend)
├── locals.tf        # Local value definitions
└── terraform.tfvars # Variable values (not committed to git if sensitive)
```

> You can name `.tf` files anything — Terraform loads ALL `.tf` files in a directory. The names above are conventions.

## Blocks

Everything in HCL is organized into **blocks**:

```hcl
block_type "label_1" "label_2" {
  argument_name = "argument_value"

  nested_block {
    nested_argument = "value"
  }
}
```

### Common Block Types

| Block | Labels | Purpose |
|-------|--------|---------|
| `terraform` | none | Settings, required providers, backend |
| `provider` | provider name | Configure a provider |
| `resource` | type, name | Create infrastructure |
| `data` | type, name | Read existing infrastructure |
| `variable` | name | Declare an input |
| `output` | name | Declare an output |
| `locals` | none | Define local values |
| `module` | name | Call a reusable module |

## Arguments & Attributes

```hcl
# Argument: you set this
resource "local_file" "example" {
  filename = "/tmp/example.txt"   # argument
  content  = "Hello"              # argument
}

# Attribute: Terraform computes this — you reference it
output "id" {
  value = local_file.example.id   # attribute reference
}
```

## Comments

```hcl
# Single-line comment (preferred)

// Also a single-line comment (C-style)

/*
  Multi-line
  comment block
*/
```

## Data Types

| Type | Example |
|------|---------|
| `string` | `"hello"` |
| `number` | `42`, `3.14` |
| `bool` | `true`, `false` |
| `list(type)` | `["a", "b", "c"]` |
| `set(type)` | `toset(["a", "b"])` |
| `map(type)` | `{ key = "value" }` |
| `object({...})` | `{ name = string, age = number }` |
| `tuple([...])` | `[string, number, bool]` |

## Official Docs

- [Configuration Language Overview](https://developer.hashicorp.com/terraform/language)
- [Syntax — Arguments & Blocks](https://developer.hashicorp.com/terraform/language/syntax/configuration)
- [Files and Directories](https://developer.hashicorp.com/terraform/language/files)
- [Type Constraints](https://developer.hashicorp.com/terraform/language/expressions/type-constraints)

## Exercises

| # | Exercise | Folder |
|---|----------|--------|
| 1 | [Block Types Demo](./01-block-types/) | See all major block types in action |
| 2 | [Multiple Files](./02-multiple-files/) | Split config across multiple `.tf` files |
