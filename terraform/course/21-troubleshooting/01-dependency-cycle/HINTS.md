# Hints — Dependency Cycle

## Hint 1
The cycle happens because `config_a` references `config_b.filename` and `config_b` references `config_a.filename`. Terraform can't decide which to create first.

## Hint 2
Ask yourself: does `config_a` really NEED the filename of `config_b`? The filename is something YOU define — it's not a computed attribute.

## Hint 3
Use `locals` to define the filenames, then reference the locals in both resources instead of referencing each other.
