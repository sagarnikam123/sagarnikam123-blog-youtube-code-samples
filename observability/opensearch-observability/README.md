# OpenSearch Observability — Docker Compose Setup

Search-centric observability: OpenSearch + Dashboards + Data Prepper (OTLP pipeline).

## Architecture

```
OTLP gRPC (:4317→21890) ─┐
                          ├→ Data Prepper → OpenSearch (:9200)
OTLP HTTP (:4318→21891) ─┘   (pipelines)       ↑
                                    OpenSearch Dashboards (:5601)
```

## Services

| Service | Image | Role |
|:--------|:------|:-----|
| opensearch | `opensearchproject/opensearch:2.19.1` | Data storage (single-node) |
| dashboards | `opensearchproject/opensearch-dashboards:2.19.1` | Observability UI |
| data-prepper | `opensearchproject/data-prepper:2.11.0` | OTLP → OpenSearch pipeline |

## Quick Start

```bash
cp .env.example .env
docker compose up -d
# OpenSearch takes ~60s; Dashboards another ~30s
./scripts/check-health.sh
```

## Access

| Endpoint | URL |
|:---------|:----|
| OpenSearch Dashboards | http://localhost:5601 |
| OpenSearch API | http://localhost:9200 |
| OTLP gRPC | localhost:4317 (→ Data Prepper :21890) |
| OTLP HTTP | localhost:4318 (→ Data Prepper :21891) |
| Data Prepper API | http://localhost:4900 |

## Data Prepper Pipelines

| Pipeline | Source | Sink (Index) |
|:---------|:-------|:-------------|
| otel-trace-pipeline | `otel_trace_source` | trace-analytics-raw |
| otel-service-map-pipeline | trace pipeline | trace-analytics-service-map |
| otel-metrics-pipeline | `otel_metrics_source` | otel-metrics-* |
| otel-logs-pipeline | `otel_logs_source` | otel-logs-* |

## Benchmark Notes

- Data Prepper is the OTLP ingestion gateway (not OpenSearch directly)
- Data Prepper listens on ports 21890 (gRPC) and 21891 (HTTP) internally, mapped to 4317/4318
- Security plugin disabled (`DISABLE_SECURITY_PLUGIN=true`)
- JVM-based: OpenSearch needs 2GB+ heap
- Service map auto-generated from trace data
- OpenSearch Dashboards → Observability plugin shows trace analytics
- Multi-arch: OpenSearch images support ARM64 + AMD64 (2.x+)

## Installation guide

- [Installation mode index](install/README.md)
- [Docker standalone](install/docker/standalone/README.md)
- [Docker Compose standalone](install/docker-compose/standalone/README.md)
- [Docker Compose cluster](install/docker-compose/cluster/README.md)
- [Helm standalone](install/helm/standalone/README.md)
- [Helm cluster](install/helm/cluster/README.md)
- [OpenSearch Kubernetes Operator](install/operator/cluster/README.md)
- [Native packages](install/binary/standalone/README.md)
