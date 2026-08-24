# Elastic Observability — Docker Compose Setup

Search-centric observability: Elasticsearch + Kibana + APM Server with native OTLP support.

## Architecture

```
OTLP gRPC (:4317) ─┐
                    ├→ APM Server (:8200) → Elasticsearch (:9200)
OTLP HTTP (:4318) ─┘                              ↑
                                          Kibana (:5601) ── queries
```

## Services

| Service | Image | Role |
|:--------|:------|:-----|
| elasticsearch | `elasticsearch:8.17.0` | Data storage (single-node) |
| kibana | `kibana:8.17.0` | Observability UI |
| apm-server | `apm-server:8.17.0` | OTLP ingestion → ES |

## Quick Start

```bash
cd install/docker-compose/standalone
cp .env.example .env
docker compose up -d
# ES takes ~60s to start, Kibana another ~30s
./scripts/check-health.sh
```

## Access

| Endpoint | URL |
|:---------|:----|
| Kibana UI | http://localhost:5601 |
| APM Server | http://localhost:8200 |
| Elasticsearch | http://localhost:9200 |
| OTLP gRPC | localhost:4317 |
| OTLP HTTP | localhost:4318 |

## OTLP Ingestion

APM Server natively accepts OTLP — no separate OTel Collector needed:
- **gRPC:** `localhost:4317`
- **HTTP:** `localhost:4318/v1/traces`, `/v1/metrics`, `/v1/logs`

Anonymous auth enabled (no API key required for benchmarking).

## Benchmark Notes

- JVM-based: Elasticsearch needs 2GB+ heap (`ES_JAVA_OPTS`)
- Security disabled (`xpack.security.enabled=false`) per benchmark methodology
- APM Server anonymous auth allows unlimited ingestion without tokens
- Single-node ES (no replication) — matches benchmark single-VM constraint
- ES takes 60-90s to fully start; APM Server waits on ES health
- Kibana Observability section shows APM, Logs, Metrics views
- Multi-arch: Elastic images support ARM64 + AMD64 (8.x+)

## Installation guide

- [Installation mode index](install/README.md)
- [Docker standalone](install/docker/standalone/README.md)
- [Docker Compose standalone](install/docker-compose/standalone/README.md)
- [Docker Compose cluster](install/docker-compose/cluster/README.md)
- [ECK Kubernetes standalone](install/operator/standalone/README.md)
- [ECK Kubernetes cluster](install/operator/cluster/README.md)
- [Helm standalone](install/helm/standalone/README.md)
- [Helm cluster](install/helm/cluster/README.md)
- [Native binary installation](install/binary/standalone/README.md)
