# OpenSearch Observability — Docker Compose standalone

Single-node OpenSearch + Dashboards + Data Prepper deployment with security disabled for benchmark simplicity.

## Quick Start

```bash
cp .env.example .env
docker compose up -d
# OpenSearch takes ~60s; Dashboards another ~30s
../../../scripts/check-health.sh
```

## Access

| Endpoint | URL |
|:---------|:----|
| OpenSearch Dashboards | http://localhost:5601 |
| OpenSearch API | http://localhost:9200 |
| OTLP gRPC | localhost:4317 (→ Data Prepper :21890) |
| OTLP HTTP | localhost:4318 (→ Data Prepper :21891) |
| Data Prepper API | http://localhost:4900 |

This is the Phase 2 benchmark path.

Official source: [OpenSearch Observability Stack](https://observability.opensearch.org/docs/deploy/).
