# Grafana LGTM installation modes

This directory covers the unified Loki + Grafana + Tempo + Mimir stack. There is no single official "LGTM chart" from Grafana Labs — the production K8s path is per-component.

| Mode | Status | Path | Notes |
|:-----|:-------|:-----|:------|
| Docker all-in-one (`grafana/otel-lgtm`) | Available | [`docker/standalone/`](docker/standalone/) | Dev/demo only; all components in one container |
| Docker Compose standalone | Available | [`docker-compose/standalone/`](docker-compose/standalone/) | Phase 1 benchmark; separate containers per component |
| Helm per-component (K8s) | Available | [`helm/components/`](helm/components/) | Production path — Loki, Mimir, Tempo, Grafana charts |
| Operators per-component (K8s) | Available | [`operator/components/`](operator/components/) | Loki Operator + Grafana Operator where supported |
| Binary unified stack | Not applicable | — | Use component binaries from individual repos |

## Reusable component guides

The repository already contains detailed per-component installation assets:

- [`../../loki/install/`](../../loki/install/) — Binary, Docker, Helm, K8s, Operator
- [`../../mimir/install/`](../../mimir/install/) — Helm, Kubernetes
- [`../../grafana/install/`](../../grafana/install/) — Binary, Helm, Kubernetes

The unified Compose stack runs all backends in monolithic single-node mode.

Official sources:
- [Grafana LGTM OSS](https://grafana.com/oss/)
- [grafana/otel-lgtm Docker image](https://grafana.com/docs/opentelemetry/docker-lgtm/)
- [Helm charts overview](https://grafana.com/docs/helm-charts/)
- [Loki Operator](https://grafana.com/docs/loki/latest/setup/install/helm/)
- [Grafana Operator](https://grafana.com/docs/grafana/latest/as-code/infrastructure-as-code/grafana-operator/)
