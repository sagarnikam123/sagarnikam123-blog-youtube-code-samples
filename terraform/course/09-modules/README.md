# Module 09 — Modules

## What is a Module?

A module is a container for multiple resources that are used together. Every Terraform configuration is a module — the root module. You can call other modules to organize and reuse code.

## Module Structure

```
modules/
└── docker-app/
    ├── main.tf          # Resources
    ├── variables.tf     # Input variables
    ├── outputs.tf       # Output values
    └── README.md        # Documentation
```

## Calling a Module

```hcl
module "web_app" {
  source = "./modules/docker-app"   # local path

  # Pass input variables
  app_name      = "web"
  image         = "nginx:alpine"
  internal_port = 80
  external_port = 8080
}

# Access module outputs
output "url" {
  value = module.web_app.access_url
}
```

## Module Sources

| Source | Example |
|--------|---------|
| Local path | `source = "./modules/mymod"` |
| Terraform Registry | `source = "hashicorp/consul/aws"` |
| GitHub | `source = "github.com/org/repo//modules/mod"` |
| S3 | `source = "s3::https://bucket.s3.amazonaws.com/mod.zip"` |
| Generic Git | `source = "git::https://example.com/repo.git"` |

## Module Best Practices

1. **Keep modules focused** — one module = one logical component
2. **Expose only what's needed** — use outputs deliberately
3. **Validate inputs** — use variable validation blocks
4. **Document** — README.md with usage examples
5. **Version** — pin module versions in production

## Official Docs

- [Modules](https://developer.hashicorp.com/terraform/language/modules)
- [Module Sources](https://developer.hashicorp.com/terraform/language/modules/sources)
- [Module Composition](https://developer.hashicorp.com/terraform/language/modules/develop/composition)
- [Publishing Modules](https://developer.hashicorp.com/terraform/language/modules/develop/publish)
- [Terraform Registry — Browse Modules](https://registry.terraform.io/browse/modules)

## Exercises

| # | Exercise | Folder |
|---|----------|--------|
| 1 | [Local Module](./01-local-module/) | Create and call a local module |
| 2 | [Module Composition](./02-module-composition/) | Compose multiple modules together |
| 3 | [Module with for_each](./03-module-for-each/) | Create multiple instances of a module |
