# Module 10 — Loops & Dynamic Blocks

## count

Create multiple copies of a resource using an integer:

```hcl
resource "docker_container" "web" {
  count = 3
  name  = "web-${count.index}"
  image = docker_image.nginx.image_id
}
```

- `count.index` — zero-based index (0, 1, 2, ...)
- Resources are addressed as `docker_container.web[0]`, `docker_container.web[1]`, etc.
- **Drawback:** removing an item from the middle causes re-indexing and recreation

## for_each

Create resources from a map or set — more stable than count:

```hcl
resource "docker_container" "apps" {
  for_each = toset(["web", "api", "worker"])
  name     = each.key
  image    = docker_image.nginx.image_id
}
```

- `each.key` — the map key or set element
- `each.value` — the map value (same as key for sets)
- Resources addressed as `docker_container.apps["web"]`
- **Advantage:** removing "api" doesn't affect "web" or "worker"

## Dynamic Blocks

Generate repeated nested blocks dynamically:

```hcl
resource "docker_container" "app" {
  name  = "app"
  image = docker_image.nginx.image_id

  dynamic "ports" {
    for_each = var.port_mappings
    content {
      internal = ports.value.internal
      external = ports.value.external
    }
  }
}
```

## Official Docs

- [count Meta-Argument](https://developer.hashicorp.com/terraform/language/meta-arguments/count)
- [for_each Meta-Argument](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each)
- [Dynamic Blocks](https://developer.hashicorp.com/terraform/language/expressions/dynamic-blocks)
- [For Expressions](https://developer.hashicorp.com/terraform/language/expressions/for)

## Exercises

| # | Exercise | Folder |
|---|----------|--------|
| 1 | [Count](./01-count/) | Create multiple resources with count |
| 2 | [For Each](./02-for-each/) | Create resources from maps and sets |
| 3 | [Dynamic Blocks](./03-dynamic-blocks/) | Generate nested blocks dynamically |
