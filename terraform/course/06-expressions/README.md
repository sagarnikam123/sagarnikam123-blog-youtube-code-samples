# Module 06 — Expressions & Operators

## What are Expressions?

Expressions are the HCL syntax for computing values. Everything on the right side of `=` is an expression.

## Types of Expressions

### Literal Values
```hcl
"hello"       # string
42            # number
true          # bool
["a", "b"]   # list
{ k = "v" }  # map
```

### References
```hcl
var.name                          # input variable
local.value                       # local value
resource_type.name.attribute      # resource attribute
data.type.name.attribute          # data source attribute
module.name.output_name           # module output
path.module                       # current module directory
path.root                         # root module directory
terraform.workspace               # current workspace name
```

### String Templates
```hcl
"Hello, ${var.name}!"                          # interpolation
"Items: %{ for item in var.list }${item}, %{ endfor }"  # directive
```

### Conditional Expression
```hcl
condition ? true_value : false_value
var.env == "prod" ? 3 : 1
```

### For Expression
```hcl
[for s in var.list : upper(s)]                    # list → list
{for k, v in var.map : k => upper(v)}             # map → map
[for s in var.list : upper(s) if s != ""]         # with filter
```

### Splat Expression
```hcl
aws_instance.servers[*].id          # equivalent to: [for s in aws_instance.servers : s.id]
```

### Operators
| Operator | Type | Example |
|----------|------|---------|
| `+`, `-`, `*`, `/`, `%` | Arithmetic | `var.count + 1` |
| `==`, `!=` | Equality | `var.env == "prod"` |
| `<`, `>`, `<=`, `>=` | Comparison | `var.port > 1024` |
| `&&`, `\|\|`, `!` | Logical | `var.a && var.b` |

## Official Docs

- [Expressions Overview](https://developer.hashicorp.com/terraform/language/expressions)
- [String Templates](https://developer.hashicorp.com/terraform/language/expressions/strings)
- [Conditional Expressions](https://developer.hashicorp.com/terraform/language/expressions/conditionals)
- [For Expressions](https://developer.hashicorp.com/terraform/language/expressions/for)
- [Splat Expressions](https://developer.hashicorp.com/terraform/language/expressions/splat)
- [Operators](https://developer.hashicorp.com/terraform/language/expressions/operators)
- [References to Values](https://developer.hashicorp.com/terraform/language/expressions/references)

## Exercises

| # | Exercise | Folder |
|---|----------|--------|
| 1 | [String Templates](./01-string-templates/) | Interpolation and directives |
| 2 | [Conditionals](./02-conditionals/) | Ternary expressions |
| 3 | [For Expressions](./03-for-expressions/) | Transform lists and maps |
