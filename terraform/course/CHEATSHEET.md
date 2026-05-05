# Terraform Cheat Sheet — Quick Reference

> Pin this. You'll use it daily.

---

## CLI Commands

### Core Workflow
```bash
terraform init                          # Download providers, initialize backend
terraform init -upgrade                 # Upgrade providers to latest allowed
terraform plan                          # Preview changes
terraform plan -out=plan.tfplan         # Save plan to file
terraform apply                         # Apply changes (prompts for confirmation)
terraform apply plan.tfplan             # Apply a saved plan (no prompt)
terraform apply -auto-approve           # Apply without confirmation
terraform destroy                       # Destroy all resources
terraform destroy -auto-approve         # Destroy without confirmation
```

### Targeting
```bash
terraform plan -target=docker_container.web       # Plan one resource
terraform apply -target=module.network            # Apply one module
terraform destroy -target=docker_container.web    # Destroy one resource
terraform apply -replace=docker_container.web     # Force recreate (replaces taint)
```

### Variables
```bash
terraform plan -var 'name=value'                          # Set a variable
terraform plan -var-file="prod.tfvars"                    # Use a var file
TF_VAR_name=value terraform plan                          # Via environment variable
```

### Formatting & Validation
```bash
terraform fmt                    # Auto-format .tf files
terraform fmt -check             # Check formatting (CI-friendly, exit code 1 if unformatted)
terraform fmt -recursive         # Format all subdirectories
terraform validate               # Validate syntax and consistency
```

### Inspection
```bash
terraform show                   # Show current state
terraform output                 # Show all outputs
terraform output -json           # Outputs as JSON
terraform output -raw name       # Raw value (no quotes, good for scripting)
terraform providers              # List providers in use
terraform graph                  # DOT format dependency graph
terraform graph | dot -Tpng > graph.png   # Render graph (needs graphviz)
terraform console                # Interactive expression evaluator
terraform version                # Show Terraform version
```

### State
```bash
terraform state list                         # List all resources
terraform state show <address>               # Show one resource
terraform state mv <old> <new>               # Rename in state
terraform state rm <address>                 # Remove from state (keeps real resource)
terraform state pull                         # Download remote state to stdout
terraform state push                         # Upload state to remote
terraform force-unlock <lock-id>             # Release stuck state lock
```

### Testing
```bash
terraform test                   # Run all .tftest.hcl files
terraform test -verbose          # Verbose test output
terraform test -filter=tests/main.tftest.hcl  # Run specific test file
```

### Workspaces
```bash
terraform workspace list         # List workspaces
terraform workspace new dev      # Create workspace
terraform workspace select dev   # Switch workspace
terraform workspace show         # Show current workspace
terraform workspace delete dev   # Delete workspace
```

---

## Variable Precedence (last wins)

```
1. default value in variable block        (lowest)
2. TF_VAR_name environment variable
3. terraform.tfvars
4. *.auto.tfvars (alphabetical order)
5. -var-file="custom.tfvars"
6. -var 'name=value'                      (highest)
```

---

## Version Constraints

| Syntax | Meaning |
|--------|---------|
| `= 3.0.2` | Exact version |
| `>= 3.0` | Minimum |
| `~> 3.0` | >= 3.0, < 4.0 (pessimistic minor) |
| `~> 3.0.2` | >= 3.0.2, < 3.1.0 (pessimistic patch) |
| `>= 3.0, < 4.0` | Range |

---

## Block Types

```hcl
terraform { }          # Settings, required_providers, backend
provider "name" { }    # Provider configuration
resource "type" "name" { }   # Create infrastructure
data "type" "name" { }       # Read existing infrastructure
variable "name" { }    # Input variable
output "name" { }      # Output value
locals { }             # Local computed values
module "name" { }      # Call a reusable module
moved { }              # Rename without destroy
import { }             # Import existing resource
removed { }            # Remove from state without destroy
check "name" { }       # Standalone validation
```

---

## References

```hcl
var.name                          # Input variable
local.name                        # Local value
resource_type.name.attribute      # Resource attribute
data.type.name.attribute          # Data source attribute
module.name.output_name           # Module output
self.attribute                    # Current resource (in provisioners)
each.key / each.value             # for_each iterator
count.index                       # count iterator
path.module                       # Current module directory
path.root                         # Root module directory
path.cwd                          # Current working directory
terraform.workspace               # Current workspace name
```

---

## Common Functions

### Strings
```hcl
upper("hello")                    # "HELLO"
lower("HELLO")                    # "hello"
trimspace("  hi  ")               # "hi"
replace("hello", "l", "L")       # "heLLo"
split(",", "a,b,c")              # ["a", "b", "c"]
join("-", ["a", "b"])             # "a-b"
format("Hi %s, %d", "Bob", 30)   # "Hi Bob, 30"
substr("hello", 0, 3)            # "hel"
startswith("hello", "he")        # true
endswith("file.tf", ".tf")       # true
regex("[0-9]+", "abc123")        # "123"
```

### Numbers
```hcl
abs(-5)          # 5
ceil(4.2)        # 5
floor(4.8)       # 4
max(5, 12, 9)    # 12
min(5, 12, 9)    # 5
pow(2, 8)        # 256
```

### Collections
```hcl
length(["a", "b"])                # 2
element(["a", "b", "c"], 1)      # "b"
contains(["a", "b"], "a")        # true
concat(["a"], ["b"])             # ["a", "b"]
flatten([["a"], ["b"]])          # ["a", "b"]
distinct(["a", "a", "b"])        # ["a", "b"]
sort(["c", "a", "b"])            # ["a", "b", "c"]
reverse(["a", "b"])              # ["b", "a"]
keys({a=1, b=2})                 # ["a", "b"]
values({a=1, b=2})               # [1, 2]
lookup({a=1}, "b", 0)            # 0
merge({a=1}, {b=2})              # {a=1, b=2}
zipmap(["a","b"], [1,2])         # {a=1, b=2}
compact(["a", "", "b"])          # ["a", "b"]
```

### Encoding
```hcl
jsonencode({a = 1})              # '{"a":1}'
jsondecode('{"a":1}')            # {a = 1}
yamlencode({a = 1})              # YAML string
base64encode("hello")            # "aGVsbG8="
base64decode("aGVsbG8=")         # "hello"
urlencode("hello world")         # "hello+world"
```

### Filesystem
```hcl
file("path/to/file")             # Read file contents
fileexists("path")               # true/false
templatefile("tpl.tftpl", vars)  # Render template
basename("/a/b/c.txt")           # "c.txt"
dirname("/a/b/c.txt")            # "/a/b"
abspath("relative/path")         # Absolute path
```

### Type Conversion
```hcl
tostring(42)                     # "42"
tonumber("42")                   # 42
tobool("true")                   # true
tolist(toset(["a","b"]))         # ["a", "b"]
toset(["a", "a", "b"])           # set: ["a", "b"]
tomap({a = 1})                   # map
try(var.optional, "default")     # First non-error value
can(regex("^[a-z]+$", var.x))   # true if expression succeeds
```

---

## Loops

```hcl
# count
resource "x" "y" {
  count = 3
  name  = "item-${count.index}"
}

# for_each with set
resource "x" "y" {
  for_each = toset(["a", "b", "c"])
  name     = each.key
}

# for_each with map
resource "x" "y" {
  for_each = var.map_variable
  name     = each.key
  value    = each.value
}

# for expression (list → list)
[for s in var.list : upper(s)]

# for expression (list → map)
{for s in var.list : s => upper(s)}

# for expression with filter
[for s in var.list : s if s != ""]

# dynamic block
dynamic "ports" {
  for_each = var.port_list
  content {
    internal = ports.value.internal
    external = ports.value.external
  }
}
```

---

## Lifecycle Rules

```hcl
lifecycle {
  create_before_destroy = true          # Zero-downtime replacement
  prevent_destroy       = true          # Block accidental destroy
  ignore_changes        = [tags, env]   # Don't track these attributes
  replace_triggered_by  = [resource.x]  # Force replace when dependency changes

  precondition {
    condition     = var.port > 1024
    error_message = "Port must be > 1024"
  }

  postcondition {
    condition     = self.id != ""
    error_message = "Resource was not created"
  }
}
```

---

## Terragrunt (1.0.2)

```bash
terragrunt init                  # Initialize
terragrunt plan                  # Plan
terragrunt apply                 # Apply
terragrunt destroy               # Destroy
terragrunt run-all plan          # Plan all modules in dependency order
terragrunt run-all apply         # Apply all modules
terragrunt run-all destroy       # Destroy in reverse order
```

```hcl
# terragrunt.hcl
include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  source = "../../modules/app"
}

dependency "network" {
  config_path = "../network"
}

inputs = {
  network_id = dependency.network.outputs.network_id
}
```

---

## File Naming Conventions

```
main.tf          # Primary resources
variables.tf     # Input variables
outputs.tf       # Output values
providers.tf     # Provider configuration
versions.tf      # Terraform and provider version constraints
locals.tf        # Local values
data.tf          # Data sources
terraform.tfvars # Variable values (don't commit secrets)
```
