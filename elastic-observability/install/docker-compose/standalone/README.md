# Elastic Observability — Docker Compose standalone

Single-node Elasticsearch + Kibana + APM Server deployment with security disabled for benchmark simplicity.

## Quick Start

```bash
cp .env.example .env
docker compose up -d
# ES takes ~60s to start, Kibana another ~30s
../../../scripts/check-health.sh
```

## Access

| Endpoint | URL |
|:---------|:----|
| Kibana UI | http://localhost:5601 |
| APM Server | http://localhost:8200 |
| OTLP gRPC | localhost:4317 |
| OTLP HTTP | localhost:4318 |

This is the Phase 2 benchmark path. APM Server natively accepts OTLP without a separate OTel Collector.

Official source: [Getting started with the Elastic Stack and Docker Compose](https://www.elastic.co/blog/getting-started-with-the-elastic-stack-and-docker-compose).
