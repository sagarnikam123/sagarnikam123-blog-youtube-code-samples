# OpenSearch Observability installation modes

| Mode | Status | Path | Notes |
|:-----|:-------|:-----|:------|
| Homebrew (macOS) | Available | [`brew/standalone/`](brew/standalone/) | OpenSearch + Dashboards via `brew services`, security disabled |
| Native packages (tar/DEB/RPM) | Available | [`binary/standalone/`](binary/standalone/) | Latest (3.8.0): OpenSearch + Dashboards + Data Prepper, with local-dev config files |
| Docker standalone | Available | [`docker/standalone/`](docker/standalone/) | Individual containers on a Docker network |
| Docker Compose standalone | Available | [`docker-compose/standalone/`](docker-compose/standalone/) | Phase 2 benchmark (single-node, security disabled) |
| Docker Compose cluster | Available | [`docker-compose/cluster/`](docker-compose/cluster/) | Multi-node local replication testing |
| Helm standalone | Available | [`helm/standalone/`](helm/standalone/) | Official observability-stack umbrella chart, single-node |
| Helm cluster | Available | [`helm/cluster/`](helm/cluster/) | Official observability-stack umbrella chart, multi-node |
| OpenSearch Kubernetes Operator | Available | [`operator/cluster/`](operator/cluster/) | Official `opensearch-k8s-operator` with CRD-managed clusters |

Official sources:
- [Install OpenSearch](https://opensearch.org/docs/latest/install-and-configure/install-opensearch/index)
- [Observability Stack (Docker Compose)](https://observability.opensearch.org/docs/deploy/)
- [Observability Stack (Kubernetes Helm)](https://observability.opensearch.org/docs/deploy/kubernetes/)
- [OpenSearch Kubernetes Operator](https://opensearch-project.github.io/opensearch-k8s-operator/)
- [Data Prepper](https://opensearch.org/docs/latest/data-prepper/)
