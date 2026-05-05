# Solution — Provider Mismatch

## Bugs Found

1. **Wrong source**: `hashicorp/docker` → should be `kreuzwerker/docker`
2. **Missing provider**: `random_pet` used but `hashicorp/random` not declared
3. **Missing provider block**: `provider "random" {}` not present

## Fixed required_providers

```hcl
required_providers {
  docker = {
    source  = "kreuzwerker/docker"
    version = "~> 3.0"
  }
  random = {
    source  = "hashicorp/random"
    version = "~> 3.6"
  }
}
```

## The Lesson
Always check the Terraform Registry for the correct `source` path. Not all providers are published by HashiCorp. The format is `<namespace>/<type>`.
