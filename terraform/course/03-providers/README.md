# Module 03 — Providers

## What is a Provider?

A provider is a plugin that Terraform uses to interact with APIs. Every resource type belongs to a provider. Providers handle authentication, API calls, and resource lifecycle.

## Provider Configuration

```hcl
terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"   # <namespace>/<type>
      version = "~> 3.0"               # version constraint
    }
  }
}

provider "docker" {
  # Configuration options (host, certs, etc.)
}
```

## Version Constraints

| Operator | Meaning | Example |
|----------|---------|---------|
| `= 3.0.2` | Exact version | Only 3.0.2 |
| `>= 3.0` | Minimum version | 3.0 or higher |
| `~> 3.0` | Pessimistic (minor) | >= 3.0, < 4.0 |
| `~> 3.0.2` | Pessimistic (patch) | >= 3.0.2, < 3.1.0 |
| `>= 3.0, < 4.0` | Range | Between 3.0 and 4.0 |

## Provider Aliases

Use aliases when you need multiple configurations of the same provider:

```hcl
provider "docker" {
  alias = "remote"
  host  = "tcp://remote-host:2376"
}

resource "docker_container" "remote_app" {
  provider = docker.remote
  # ...
}
```

## Provider Lock File

`terraform init` generates `.terraform.lock.hcl` — this locks provider versions for reproducible builds. Commit this file to version control in real projects (excluded in this course for cleanliness).

## Official Docs

- [Provider Configuration](https://developer.hashicorp.com/terraform/language/providers/configuration)
- [Provider Requirements](https://developer.hashicorp.com/terraform/language/providers/requirements)
- [Dependency Lock File](https://developer.hashicorp.com/terraform/language/files/dependency-lock)
- [Terraform Registry — Docker Provider](https://registry.terraform.io/providers/kreuzwerker/docker/latest/docs)

## Exercises

| # | Exercise | Folder |
|---|----------|--------|
| 1 | [Multiple Providers](./01-multiple-providers/) | Use Docker + Random + Local together |
| 2 | [Provider Aliases](./02-provider-aliases/) | Multiple configs of the same provider |
| 3 | [Provider Versions](./03-provider-versions/) | Version constraints in action |
