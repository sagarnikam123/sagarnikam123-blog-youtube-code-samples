# Grafana Tempo installation modes

| Mode | Status | Path | Notes |
|:-----|:-------|:-----|:------|
| Binary standalone (monolithic) | Available | [`binary/`](binary/) | Single binary, local filesystem |
| Docker standalone | Available | [`docker/`](docker/) | Single container monolithic mode |
| Docker Compose (+ Grafana) | Available | [`docker-compose/`](docker-compose/) | Tempo + Grafana with pre-provisioned datasource |
| Helm monolithic | Available | [`helm/monolithic/`](helm/monolithic/) | `grafana/tempo` chart, single-node K8s |
| Helm distributed | Available | [`helm/distributed/`](helm/distributed/) | `grafana/tempo-distributed` chart, production scaling |
| Tempo Operator | Available | [`operator/`](operator/) | `TempoStack` CRD-managed deployment |

## Deployment modes

- **Monolithic**: All components in one process. Good for dev/testing or small-scale.
- **Distributed (microservices)**: Separate distributor, ingester, querier, compactor. Scales horizontally. Requires object storage.

## Trace ingestion protocols

| Protocol | Default Port |
|:---------|:-------------|
| OTLP gRPC | 4317 |
| OTLP HTTP | 4318 |
| Jaeger thrift HTTP | 14268 |
| Jaeger thrift compact (UDP) | 6831 |
| Zipkin | 9411 |

Official sources:
- [Tempo documentation](https://grafana.com/docs/tempo/latest/)
- [Deploy Tempo](https://grafana.com/docs/tempo/latest/set-up-for-tracing/setup-tempo/deploy/)
- [Helm charts](https://grafana.com/docs/tempo/latest/setup/helm-chart/)
- [Tempo Operator](https://grafana.com/docs/tempo/latest/set-up-for-tracing/setup-tempo/deploy/kubernetes/operator/)
