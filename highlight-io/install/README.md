# Highlight.io installation modes

| Mode | Status | Path | Notes |
|:-----|:-------|:-----|:------|
| Docker Compose hobby (self-hosted) | Available | [`docker-compose/hobby/`](docker-compose/hobby/) | Only official self-hosted method; Phase 2 benchmark |
| Docker Compose development | Available | [`docker-compose/dev/`](docker-compose/dev/) | For contributing; hot-reload and source mounts |
| Enterprise self-hosted | Not publicly documented | — | Contact Highlight/LaunchDarkly for custom deployment |
| Binary | Not published | — | Multi-service platform; no single binary |
| Kubernetes / Helm | Not published | — | No official Helm chart or K8s manifests |
| Operator | Not published | — | No upstream operator |

## Key facts

- The **only** supported self-hosted path is Docker Compose from the official GitHub repository.
- Highlight.io does not publish a standalone binary, Helm chart, or Kubernetes manifests.
- The hobby deployment fetches and builds all services from source using Docker.
- Minimum requirements: 8 GB RAM, 4 CPUs, 64 GB disk, Docker 25.0+.
- Acquired by LaunchDarkly in 2025; open-source repo remains active.

Official sources:
- [GitHub — highlight/highlight](https://github.com/highlight/highlight)
- [Self-host overview](https://github.com/highlight/highlight/blob/main/docs-content/getting-started/self-host/1_overview.md)
