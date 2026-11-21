# Parseable installation guide

Parseable is an open-source, Rust-based telemetry data lake platform for logs, metrics, and traces. It stores all signals as Apache Parquet on object storage or local disk.

## Available modes

| Mode | Status | Guide |
|:-----|:-------|:------|
| Binary standalone | Available | [`install/binary/standalone/`](install/binary/standalone/) |
| Docker standalone | Available | [`install/docker/standalone/`](install/docker/standalone/) |
| Docker Compose standalone | Available | [`install/docker-compose/standalone/`](install/docker-compose/standalone/) |
| Docker Compose distributed | Available | [`install/docker-compose/distributed/`](install/docker-compose/distributed/) |
| Helm standalone | Available | [`install/helm/standalone/`](install/helm/standalone/) |
| Helm distributed | Available | [`install/helm/distributed/`](install/helm/distributed/) |
| Kubernetes Operator | Available | [`install/operator/cluster/`](install/operator/cluster/) |

The Docker Compose standalone setup is the Phase 1 benchmark deployment.

## Key characteristics

- Single Rust binary, no JVM, no GC pauses
- Apache Parquet on object storage (S3/MinIO/GCS/Azure) or local disk
- Native OTLP ingestion (HTTP) for logs, metrics, traces
- SQL query engine (PromQL requires Enterprise)
- APM service views require Enterprise
- HA/distributed mode requires Enterprise for full features
- AGPL v3 license

Official site: [parseable.com](https://www.parseable.com/)
