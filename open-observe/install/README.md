# OpenObserve installation modes

| Mode | Status | Path | Notes |
|:-----|:-------|:-----|:------|
| Binary standalone | Available | [`binary/standalone/`](binary/standalone/) | Single binary, local disk, no external deps |
| Docker standalone | Available | [`docker/standalone/`](docker/standalone/) | Single container, local mode |
| Docker Compose standalone | Available | [`docker-compose/standalone/`](docker-compose/standalone/) | Phase 1 benchmark |
| Helm standalone | Available | [`helm/standalone/`](helm/standalone/) | Single-node Kubernetes, local mode |
| Helm cluster / HA | Available | [`helm/cluster/`](helm/cluster/) | Multi-node Kubernetes, object storage + PostgreSQL + NATS |
| Configuration operator | Available (enterprise) | [`operator/cluster/`](operator/cluster/) | Manages CRD configuration objects, not the platform |
| Terraform module | Available (enterprise) | — | Uses the Helm chart; see [Terraform docs](https://openobserve.ai/docs/enterprise-setup/terraform/) |

## Architecture modes

- **Single-node / local mode** (`ZO_LOCAL_MODE=true`): SQLite metadata + local disk Parquet storage. No external dependencies. Can handle 2+ TB/day on one machine.
- **HA / cluster mode** (`ZO_LOCAL_MODE=false`): PostgreSQL metadata + object storage (S3/GCS/MinIO/Swift) + NATS coordination. Multiple role-specific nodes (Router, Ingester, Querier, Compactor, Scheduler).

Official sources:
- [Getting started](https://openobserve.ai/docs/getting-started/)
- [Architecture](https://openobserve.ai/docs/architecture/)
- [HA deployment](https://openobserve.ai/docs/administration/deployment/ha-deployment/)
- [Helm chart](https://github.com/openobserve/openobserve-helm-chart)
- [Docker Hub](https://hub.docker.com/r/openobserve/openobserve)
- [GitHub releases](https://github.com/openobserve/openobserve/releases)
