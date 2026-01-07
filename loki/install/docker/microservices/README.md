# Loki Microservices - Docker

Full microservices mode with each component running separately.

## Components

- Distributor
- Ingester
- Querier
- Query Frontend
- Query Scheduler
- Compactor
- Index Gateway
- Ruler
- Bloom Gateway (optional)

## When to Use

| ✅ Good For | ❌ Not For |
|-------------|-----------|
| Large scale (1TB+/day) | Small/medium deployments |
| Fine-grained scaling | Simple setups |
| Maximum flexibility | Quick prototyping |

## Status

🚧 Coming soon - use `helm/` or `k8s/` for Microservices deployments.
