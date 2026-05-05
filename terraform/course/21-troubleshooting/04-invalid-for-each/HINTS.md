# Hints — Invalid for_each

## Hint 1
`for_each` requires its keys to be known at plan time. `random_integer.count.result` is only known after apply — Terraform can't plan resources it doesn't know the count of.

## Hint 2
Replace the random-dependent for_each with a static variable that you control:

```hcl
variable "config_names" {
  type    = set(string)
  default = ["config-0", "config-1", "config-2"]
}
```

## Hint 3
If you truly need a dynamic count, use `count` with a variable instead of `for_each` with a computed value. Or use a two-step apply: first create the random value, then use it.
