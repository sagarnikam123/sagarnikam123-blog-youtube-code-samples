# Parseable installation modes

| Mode | Status | Path | Notes |
|:-----|:-------|:-----|:------|
| Binary standalone | Available | [`binary/standalone/`](binary/standalone/) | Single Rust binary, local disk |
| Docker standalone | Available | [`docker/standalone/`](docker/standalone/) | Single container, local store |
| Docker Compose standalone | Available | [`docker-compose/standalone/`](docker-compose/standalone/) | Phase 1 benchmark |
| Docker Compose distributed | Available | [`docker-compose/distributed/`](docker-compose/distributed/) | Multi-node + object storage |
| Helm standalone | Available | [`helm/standalone/`](helm/standalone/) | K8s single-node, local PVC |
| Helm distributed | Available | [`helm/distributed/`](helm/distributed/) | K8s multi-node + object storage |
| Kubernetes Operator | Available | [`operator/cluster/`](operator/cluster/) | Official CRD-managed clusters |

## Architecture modes

- **Standalone** (`local-store`): Single ingest + query node, local disk Parquet. No external deps.
- **Distributed** (`s3-store`): Separate ingestor/querier nodes, object storage required. HA features need Enterprise.

Official sources:
- [Installation](https://www.parseable.com/docs/self-hosted/installation)
- [Helm chart](https://charts.parseable.com/charts/parseable/)
- [Kubernetes Operator](https://github.com/parseablehq/operator)
- [Docker Hub](https://hub.docker.com/r/parseable/parseable)
- [GitHub releases](https://github.com/parseablehq/parseable/releases)
- [Editions comparison](https://www.parseable.com/docs/editions/compare)
