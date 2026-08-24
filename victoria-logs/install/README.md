# VictoriaLogs installation modes

VictoriaLogs is a high-performance log database. This directory covers component-level deployment (logs only). For the full VictoriaMetrics observability stack (metrics + logs + traces + Grafana), see [`../victoria-metrics/install/`](../victoria-metrics/install/).

| Mode | Status | Path | Notes |
|:-----|:-------|:-----|:------|
| Binary standalone | Available | [`binary/`](binary/) | Single binary + Fluent Bit + vmalert + AlertManager |
| Docker Compose | Available | [`docker/`](docker/) | Full local stack with Grafana |
| Helm single-node | Available | [`helm/`](helm/) | `victoria-logs-single` chart |
| Helm cluster | Available | [`helm-cluster/`](helm-cluster/) | `victoria-logs-cluster` chart (distributed) |
| Kubernetes Operator | Available | [`operator/`](operator/) | `VLogs` CRD via VictoriaMetrics Operator |

## Architecture modes

- **Single-node**: One `victoria-logs-prod` binary or single Helm chart. Scales vertically.
- **Cluster**: Separate vlinsert + vlselect + vlstorage. Scales horizontally.

## Related docs

- [VictoriaLogs vs Loki Comparison](../docs/VictoriaLogs_vs_Loki_Comparison.md)
- [Production Architecture](../docs/production-architecture.md)

Official sources:
- [VictoriaLogs Quick Start](https://docs.victoriametrics.com/victorialogs/quickstart/)
- [Helm single chart](https://docs.victoriametrics.com/helm/victorialogs-single/)
- [Helm cluster chart](https://docs.victoriametrics.com/helm/victoria-logs-cluster/)
- [VLogs operator resource](https://docs.victoriametrics.com/operator/resources/vlogs/)
- [GitHub](https://github.com/VictoriaMetrics/VictoriaLogs)
