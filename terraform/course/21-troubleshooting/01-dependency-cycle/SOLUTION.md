# Solution — Dependency Cycle

## The Problem
`config_a` references `config_b.filename` → creates dependency A→B
`config_b` references `config_a.filename` → creates dependency B→A
Result: A→B→A = cycle

## The Fix
Extract the filenames into `locals` so neither resource depends on the other:

```hcl
locals {
  file_a = "${path.module}/output/config-a.txt"
  file_b = "${path.module}/output/config-b.txt"
}

resource "local_file" "config_a" {
  filename = local.file_a
  content  = "Config A knows about: ${local.file_b}"
}

resource "local_file" "config_b" {
  filename = local.file_b
  content  = "Config B knows about: ${local.file_a}"
}
```

## The Lesson
Only reference another resource's attributes when you genuinely need a **computed** value (like an ID or IP). If the value is something you control (like a filename), put it in `locals`.
