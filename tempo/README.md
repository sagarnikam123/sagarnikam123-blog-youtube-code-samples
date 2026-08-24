# Grafana Tempo

Grafana Tempo is a high-scale, cost-effective distributed tracing backend. It requires only object storage to operate and integrates natively with Grafana for trace visualization.

## Installation modes

| Mode | Guide |
|:-----|:------|
| Binary standalone (monolithic) | [`install/binary/`](install/binary/) |
| Docker standalone | [`install/docker/`](install/docker/) |
| Docker Compose | [`install/docker-compose/`](install/docker-compose/) |
| Helm monolithic | [`install/helm/monolithic/`](install/helm/monolithic/) |
| Helm distributed | [`install/helm/distributed/`](install/helm/distributed/) |
| Tempo Operator (K8s) | [`install/operator/`](install/operator/) |

## Key facts

- Requires only object storage (S3/GCS/MinIO/Azure) for production
- Local filesystem backend available for dev/testing
- Accepts OTLP, Jaeger, Zipkin, and Kafka natively
- TraceQL query language
- Metrics generator: produces RED metrics from traces → remote_write to Mimir/Prometheus
- Apache 2.0 (AGPL for some components)
- Docker image: `grafana/tempo`

Official site: [grafana.com/oss/tempo](https://grafana.com/oss/tempo/)
