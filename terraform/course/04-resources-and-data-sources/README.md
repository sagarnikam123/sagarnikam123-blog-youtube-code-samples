# Module 04 — Resources & Data Sources

## Resources

A resource block declares a piece of infrastructure. Terraform manages its full lifecycle: create, read, update, delete (CRUD).

```hcl
resource "<PROVIDER_TYPE>" "<LOCAL_NAME>" {
  argument1 = "value1"
  argument2 = "value2"
}
```

- `PROVIDER_TYPE` — e.g., `docker_container`, `local_file`, `random_pet`
- `LOCAL_NAME` — your label for referencing this resource elsewhere

### Resource Behavior

| Action | When |
|--------|------|
| **Create** | Resource in config but not in state |
| **Update** | Resource in config AND state, but arguments changed |
| **Destroy** | Resource in state but removed from config |
| **Re-create** | A "force new" argument changed (can't update in-place) |

### Referencing Resources

```hcl
# Syntax: <resource_type>.<local_name>.<attribute>
docker_image.nginx.image_id
random_pet.name.id
local_file.config.content
```

## Data Sources

Data sources let you **read** information from existing infrastructure or compute values. They don't create anything.

```hcl
data "<PROVIDER_TYPE>" "<LOCAL_NAME>" {
  # query arguments
}

# Reference: data.<type>.<name>.<attribute>
```

## Implicit vs Explicit Dependencies

```hcl
# Implicit — Terraform detects the reference automatically
resource "docker_container" "app" {
  image = docker_image.nginx.image_id   # implicit dependency
}

# Explicit — use depends_on when there's no direct reference
resource "null_resource" "wait" {
  depends_on = [docker_container.app]
}
```

## Official Docs

- [Resources](https://developer.hashicorp.com/terraform/language/resources)
- [Resource Behavior](https://developer.hashicorp.com/terraform/language/resources/behavior)
- [Data Sources](https://developer.hashicorp.com/terraform/language/data-sources)
- [Resource Dependencies](https://developer.hashicorp.com/terraform/language/resources/behavior#resource-dependencies)
- [HTTP Data Source](https://registry.terraform.io/providers/hashicorp/http/latest/docs/data-sources/http)
- [External Data Source](https://registry.terraform.io/providers/hashicorp/external/latest/docs/data-sources/external)

## Exercises

| # | Exercise | Folder |
|---|----------|--------|
| 1 | [Resource Basics](./01-resource-basics/) | Create, reference, and destroy Docker resources |
| 2 | [Data Sources](./02-data-sources/) | Read data with http, local_file, and external data sources |
| 3 | [Dependencies](./03-dependencies/) | Implicit and explicit dependency ordering |
