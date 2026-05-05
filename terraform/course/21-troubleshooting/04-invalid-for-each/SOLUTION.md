# Solution — Invalid for_each

## The Problem
`for_each` needs to know its keys at plan time. `random_integer.count.result` is computed at apply time — Terraform can't determine the resource addresses during planning.

## Fix Option 1: Use a static variable
```hcl
variable "config_names" {
  type    = set(string)
  default = ["config-0", "config-1", "config-2"]
}

resource "local_file" "configs" {
  for_each = var.config_names
  filename = "${path.module}/output/${each.key}.txt"
  content  = "Config file: ${each.key}"
}
```

## Fix Option 2: Use count with a variable
```hcl
variable "config_count" {
  type    = number
  default = 3
}

resource "local_file" "configs" {
  count    = var.config_count
  filename = "${path.module}/output/config-${count.index}.txt"
  content  = "Config file: config-${count.index}"
}
```

## The Lesson
`for_each` keys must be known at plan time. Use variables you control, not computed resource attributes. If you need dynamic counts, use `count` with a variable or a two-phase approach.
