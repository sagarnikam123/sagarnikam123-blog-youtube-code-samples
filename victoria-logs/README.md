# VictoriaLogs

VictoriaLogs is a high-performance, lightweight, zero-config, schema-free database for logs. This directory contains component-level deployment guides for VictoriaLogs specifically.

For the full VictoriaMetrics observability stack (VM + VL + VT + Grafana), see [`../victoria-metrics/`](../victoria-metrics/).

## Installation modes

| Mode | Guide |
|:-----|:------|
| Binary standalone | [`install/binary/`](install/binary/) |
| Docker Compose | [`install/docker/`](install/docker/) |
| Helm single-node | [`install/helm/`](install/helm/) |
| Helm cluster | [`install/helm-cluster/`](install/helm-cluster/) |
| Kubernetes Operator | [`install/operator/`](install/operator/) |

## Documentation

- [VictoriaLogs vs Loki Comparison](docs/VictoriaLogs_vs_Loki_Comparison.md)
- [Production Architecture](docs/production-architecture.md)
